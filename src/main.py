#!/usr/bin/env python3
from data import SetPages
from pprint import pprint


class PagePress(object):
	def __init__(self) -> None:
		self._sett = SetPages()


if __name__ == '__main__':
	page = PagePress()
