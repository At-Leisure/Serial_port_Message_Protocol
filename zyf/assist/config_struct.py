from dataclasses import dataclass
from collections import OrderedDict
from typing import Any
import yaml
from functools import cached_property
from pprint import pprint
from copy import deepcopy


class Config:

    def __init__(self, yaml_path: str = None):
        self.yaml_path = yaml_path
        self._configure = {
            'parameters': [],
            'settings': {
                'send': {
                    'frame head': '<A>',
                    'frame tail': '</A>'
                },
                'recv': {
                    'frame head': '<B>',
                    'frame tail': '</B>'
                }
            }
        }
        if yaml_path:
            self.load(yaml_path)

    @property
    def parameters(self) -> OrderedDict[str, float]:
        return self._configure['parameters']

    @parameters.setter
    def parameters(self, x):
        self._configure['parameters'] = OrderedDict(x)

    @property
    def settings(self):
        return self._configure['settings']

    # @settings.setter
    # def settings(self, x):
    #     self._configure['settings'] = x

    def load(self, yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            self._configure = yaml.safe_load(f)
        self._configure['parameters'] = OrderedDict(self._configure['parameters'])

    def show(self):
        pprint(self._configure)

    def dump(self, path) -> str:

        x = deepcopy(self._configure)
        x['parameters'] = [[k, v] for k, v in x['parameters'].items()]  # 从OrderedDict转回list
        print(x)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(x, f)


if __name__ == '__main__':
    c = Config('config.yaml')
    print(c._configure)
    c.dump('./a.yaml')
