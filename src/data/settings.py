#!/usr/bin/env python3
from pathlib import Path


PATH = Path(__file__).resolve().parent.parent


class Settings(object):
	def __init__(self) -> None:
		self._path = PATH

	@property
	def path(self) -> str:
		return self._path
