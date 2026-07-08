#!/usr/bin/env python3
import os


class ConfFile(object):
    """Configuration file object.

    Configuration files have extensions such as '.desktop', '.conf', or '.INI'
    . This object converts these files into a dictionary to facilitate access 
    to their values.
    """
    def __init__(self, url: str) -> None:
        """Class constructor

        Initialize class properties.

        :param url:
            String from a configuration file like: "/path/file.conf"
        """
        self.__url = os.path.abspath(url)
        self.__content = None

    @property
    def content(self) -> dict:
        """Contents of a configuration file as a dictionary

        Example:
        >>> conf_file = ConfFile(
        ... url='/usr/share/applications/firefox.desktop')
        >>> conf_file.content['[Desktop Entry]']['Name']
        'Firefox Web Browser'
        >>> conf_file.content['[Desktop Entry]']['Type']
        'Application'
        >>> for key in conf_file.content.keys():
        ... print(key)
        ...
        [Desktop Entry]
        [Desktop Action new-window]
        [Desktop Action new-private-window]
        >>>
        >>> conf_file.content['[Desktop Action new-window]']['Name']
        'Open a New Window'
        """
        if not self.__content:
            self.__parse_file_to_dict()
        return self.__content

    @property
    def url(self) -> str:
        """URL of the configuration file

        The URL used to construct this object, like: "/path/file.conf".

        :return: String from a configuration file
        """
        return self.__url

    def update_file(self) -> None:
        """Updates the file with the new, modified settings."""
        self.content
        
        txt = ''
        for name in self.__content.keys():
            if name == '[': continue

            txt += f'{name}\n'
            for key, value in self.__content[name].items():
                txt += f'{key}={value}\n'
            txt += f'\n'

        with open(self.__url, 'w+') as f:
            f.write(txt.replace('\n\n', '\n'))

        self.__parse_file_to_dict()

    def __parse_file_to_dict(self) -> None:
        with open(self.__url, 'r') as ini_file:
            ini_text = ini_file.read()

        self.__content = {}
        for scope in ini_text.split('['):
            if not scope.strip().startswith('#'):
                scope = f'[{scope.strip()}'

            header, key, value = '', '', ''
            for line in scope.split('\n'):
                if line and not line.strip().startswith('#'):
                    line = line.strip()

                    if line.startswith('['):
                        header = line
                        self.__content[header] = {}

                    elif '=' in line:
                        key, value = line.split('=')
                        self.__content[header][key] = value

                    else:
                        value = self.__content[header][key] + ' ' + line
                        self.__content[header][key] = value
