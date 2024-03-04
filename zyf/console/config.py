import yaml
from icecream import ic
import pprint

PROJECT_VERSION = 2  # 程序的版本信息

class YamlStyleError(Exception):
    """ yaml格式不符合 """
    
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class Config:
    """ 方便地加载和保存配置文件 """

    def __init__(self, yaml_path: str = None):
        """ 初始化，yaml_path可以为空的"""
        self.yaml_path: str
        self._data: dict
        if yaml_path:
            self.load(yaml_path)

    def load(self, yaml_path: str = None):
        """ 通过指定新的配置文件路径来重新加载配置 """
        self.yaml_path = yaml_path
        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            self._data = yaml.safe_load(f)
        if self.is_compliant:
            print(f'[信息]成功加载yaml文件 from {self.yaml_path}')
        else:
            raise YamlStyleError('yaml格式错误')

    def dump(self, yaml_path: str = None):
        """ 如果未指定另存路径，则默认保存到原始文件 """
        path = self.yaml_path if yaml_path is None else yaml_path
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self._data, f, allow_unicode=True)  # allow_unicode=True 支持中文
        print(f'Yaml Saved as {path}')

    def __getitem__(self, keys: str | tuple):
        """ Only Read 便捷地读取数据
        >>> self['k1']
        >>> self['k1','k2'] # self['k1']['k2']"""
        if isinstance(keys, str):
            return self._data[keys]
        elif isinstance(keys, tuple):
            ret = self._data
            for k in keys:
                ret = ret[k]
            return ret

    def __setitem__(self, keys, v):
        # pprint.pprint(self._data)
        obj = self._data
        # 获取倒数第二个对象的引用
        for i in keys[:-1]:
            obj = obj[i]
        # 对最后一个对象进行赋值
        obj[keys[-1]] = v
        
    
    @property
    def n_value_group(self) -> int:
        """ 几个数值组 """
        return len(self['parameter', 'values'])

    @property
    def n_param_group(self) -> int:
        """ 几个参数 """
        return len(self['parameter', 'infos'])

    @property
    def is_compliant(self) -> bool:
        """ 检查数据的合规性 """
        compliant = []
        parameters_len = None

        def is_include(key, dict_) -> bool:
            """ 检测key是否存在于dict_中，并输出对应的警告提示信息 """
            flag: bool = True if key in dict_ else False
            compliant.append(flag)
            if not flag:
                print(f'[警告]`{key}` was not included in {self.yaml_path}')
            return flag

        def is_include2(bool_, warn_='Some errors have occurred') -> bool:
            """ 检测bool_是否是True，并输出对应的警告提示信息 """
            flag: bool = bool_
            compliant.append(flag)
            if not flag:
                print(f'[警告]{warn_} in {self.yaml_path}')
            return flag
        if is_include('file info', self._data):  # 文件功能地描述
            is_include('title', self['file info'])
            is_include('description', self['file info'])

        if is_include('project info', self._data):  # 程序信息的描述
            if is_include('version', self['project info']):
                is_include2(int(str(self['project info', 'version']).split('.')[0]) == PROJECT_VERSION)

        if is_include('initial', self._data):  # 串口初始化的描述
            is_include('includes', self['initial'])
            is_include('coding', self['initial'])
        if is_include('parameter', self._data):  # 参数信息的描述
            if is_include('infos', self['parameter']):  # 参数名字
                parameters_len = len(self['parameter', 'infos'])
                for info in self['parameter', 'infos']:
                    is_include('title', info)
                    is_include('description', info)
                    is_include('extern', info)
                    is_include('define', info)
                    is_include('alias', info)
            if is_include('values', self['parameter']):  # 参数数值
                for value in self['parameter', 'values']:
                    is_include('title', value)
                    is_include('description', value)
                    if is_include('details', value) and not parameters_len is None:
                        is_include2(parameters_len == len(value['details']),
                                    f'`{value["title"]}`参数在上下文中的个数不相互一致')
                        is_include2(all(isinstance(v, (int, float)) for v in value['details']),
                                    f'`{value["title"]}`参数的类型不完全符合(int,float)')
        if is_include('setting', self._data):  # 传输配置
            if is_include('send', self['setting']):
                is_include('frame head', self['setting', 'send'])
                is_include('frame tail', self['setting', 'send'])
            if is_include('recv', self['setting']):
                is_include('frame head', self['setting', 'recv'])
                is_include('frame tail', self['setting', 'recv'])
                
        is_include('delay_ms',self._data)

        ic(all(compliant))
        return all(compliant)
