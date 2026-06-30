#!/usr/bin/env python3
from data import Settings


class PagePress(object):
	def __init__(self) -> None:
		self._sett = Settings()
		print(self._sett.path)


if __name__ == '__main__':
	page = PagePress()
