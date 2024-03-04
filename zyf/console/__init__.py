import os
import re
from functools import wraps
from typing import Literal
from icecream import ic
from pathlib import Path
import shutil
import inspect
import enum
import serial as ser
from copy import deepcopy
from typing import Any, NoReturn
from .config import Config
from zyf.assist import type_check

MAN_HISTORY_LEN = 7
""" 保留历史的最大个数 """

CHAR_N = '\n'
CHAR_N_ = r'\n'
CHAR_T = '\t'
CodingFiles = ('main.c', 'serial_order.h', 'serial_order.c')
CodingFileNames = Literal['main.c', 'serial_order.h', 'serial_order.c']  # 生成文件名
""" - `main.c`示例主程序，仅包含调用的说明
- `serial_order.c`各种辅助函数的实现
- `serial_order.h`各种类型的声明"""

MAX_PARAM_NUMBER: int = None
""" 每个命令的最多能有的参数个数 """


class Orders(enum.Enum):
    VALUE, OTHER = range(2)


def replace_type(k: Literal['char', 'int', 'float', 'double']):
    replace_dict = {
        'char': '%c',
        'int': '%d',
        'float': '%f',
        'double': '%lf'
    }
    return replace_dict[k]


def add_writable(method):
    """ Console类仅在执行类方法时是可读的 """
    @wraps(method)
    def wrapper(*args, **kwargs):
        instance: Console = args[0]  # 获取Console类对象
        if not isinstance(instance, Console):
            raise TypeError()
        instance._set_writable(True)  # 关闭只读属性
        method(*args, **kwargs)  # 执行类方法
        instance._set_writable(False)  # 开启只读属性
    return wrapper


class Console:

    @add_writable
    def __init__(self) -> None:
        self.data = Config()
        self.serial = ser.Serial()
        self.group_index = 0  # 当前使用第几个参数组
        self._loading_path = './config/load_history.txt'
        self.loading_histories: tuple[str] = []  # 越往后越新
        self.dct = {
            'write encoding': 'ASCII',
            'read encoding': 'ASCII'
        }

    def load(self, yaml_path: str):
        self.data.load(yaml_path)
        self.loading_histories.append(str(yaml_path))
        self.dump_into_history()

    @add_writable
    def set_serial(self, d: dict[str, Any]) -> Exception:
        """ 更改串口设置

        >>> port: str | None = None #串口设备路径,
        >>> baudrate: int = 9600, #串口通信的波特率
        >>> bytesize: int = 8, #数据帧的字节大小
        >>> parity: str = "N", #奇偶校验位
        >>> stopbits: float = 1, #停止位的数量
        >>> timeout: float | None = None, #读取数据的超时时间，单位为秒
        >>> xonxoff: bool = False, #控制软件流控协议
        >>> rtscts: bool = False, #控制硬件流控协议
        >>> write_timeout: float | None = None, #写入数据的超时时间，单位为秒
        >>> dsrdtr: bool = False, #是否使用DSR/DTR信号线进行流控
        >>> inter_byte_timeout: float | None = None #两个字节之间的超时时间,
        >>> exclusive: float | None = None #设置串口的独占模式
        #
        >>> write encoding: Literal['ASCII','UTF-8'] = 'ASCII'"""
        try:
            for k, v in d.items():
                if k in self.dct.keys():
                    self.dct[k] = v
                else:
                    setattr(self.serial, k, v)
        except Exception as e:
            raise e
        ic(d)

    @add_writable
    def load_from_history(self, x: int, from_path=False):
        """ 从load_history中加载数据 """
        if from_path:
            if not os.path.isfile(self._loading_path):
                with open(self._loading_path, 'w', encoding='utf-8'):
                    pass
            with open(self._loading_path, 'r', encoding='utf-8') as f:
                self.loading_histories = [fn.strip() for fn in f.readlines()]
                
        yaml_path = Path(self.loading_histories[x])
        if yaml_path.is_file():
            self.data.load(yaml_path)
        else: #文件不存在，打开默认文件
            self.load('./data/test.yaml')
            

    @add_writable
    def dump_into_history(self):
        len_ = min(len(self.loading_histories), MAN_HISTORY_LEN)
        with open(self._loading_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.loading_histories[len(self.loading_histories)-len_:]))

    def _set_writable(self, x: bool):
        if not isinstance(x, bool):
            raise TypeError(f'type of x is {type(x)} instead of boolean')
        super().__setattr__('_is_writable', x)

    def __setattr__(self, __name: str, __value: Any) -> None:
        self._is_writable: bool
        if self._is_writable:
            super().__setattr__(__name, __value)
        else:
            raise NotImplementedError('Console类对外是只读的')

    @property
    def yaml_path(self):
        return deepcopy(self.data.yaml_path)

    def _serial_write(self, info: str) -> Exception | None:
        print(f'[send]: {info}')
        try:
            self.serial.write(info.encode(self.dct['write encoding']))
        except ser.PortNotOpenError as e:
            print(e.args)
            return e

    @type_check
    def make_normal_order(self, order: str, *, do_send=True) -> tuple[str, Exception]:
        """  """
        exception = None
        if do_send:
            exception = self._serial_write(order)
        return order, exception

    @type_check
    def make_shortcut_order(self, shortcut_id: int, *, do_send=True) -> tuple[str, Exception]:
        """  """
        order = f'[{Orders.OTHER.value}:{shortcut_id}]'
        return self.make_normal_order(order, do_send=do_send)

    @type_check
    def make_param_order(self, alias: str, v: float | int, *, do_send=True) -> tuple[str, Exception]:
        """ API: 获取调参数的命令的文本 

        `do_send`是否同时进行发送

        ## Return
        order 命令文本
        err Exception对象"""
        order = f"[0:{[p['alias'] for p in self.data['parameter','infos']].index(alias)},{v}]"
        o, exception = self.make_normal_order(order, do_send=do_send)

        if not exception:  # 发送不报错，确认更改数值
            # if True:
            param_index = [a['alias'] for a in self.data['parameter', 'infos']].index(alias)
            ic(param_index)
            self.data['parameter', 'values', self.group_index, 'details', param_index] = v
        return order, exception

    @property
    def current_loading(self) -> str:
        """ 当前加载的yaml配置文件 """
        return self.loading_histories[-1]

    def save_codings(self):
        """ API: 将代码文件保存到指定文件夹下 """
        folder = Path('./build') / self.current_loading.replace('\\', '/').split('/')[-1]
        print(folder)
        # 创建文件夹
        if not folder.is_dir():
            folder.mkdir()
        # 写入代码
        for fn in CodingFiles:
            with open(folder/fn, 'w', encoding='utf-8') as f:
                f.write(self.coding(fn))
        # -------------------------------------------- headfile.h ------------------------------------------------
        with open(folder/'headfile.h', 'w', encoding='utf-8') as f:
            f.write(f"""#ifndef __HEADFILE_H__
#define __HEADFILE_H__

typedef char uint8;
typedef unsigned short uint16;
typedef unsigned int uint32;

uint32 wireless_uart_send_buff(uint8 *buff, uint16 len);
uint32 wireless_uart_read_buff(uint8 *buff, uint32 len);

{f'{CHAR_N}'.join(sc['define'] for sc in self.data['shortcut'])}

{CHAR_N.join(e for e in set([param['extern'] for param in self.data['parameter', 'infos']]))}

#endif""")

    def coding(self, fn: CodingFileNames) -> str:
        """ API: 返回对应文件名的C语言代码 """
        aliases = [param['alias'] for param in self.data['parameter', 'infos']]
        definitions = [param['define'] for param in self.data['parameter', 'infos']]
        externs = set([param['extern'] for param in self.data['parameter', 'infos']])
        max_len = max(len(alias) for alias in aliases)
        shortcut_definitions = [sc['define'] for sc in self.data['shortcut']]
        shortcut_function_name = [re.findall(r'(?<=\s)\w+(?=\()', sd)[0] for sd in shortcut_definitions]
        shortcut_param_type = [re.findall(r'\w+(?=\s\w+=)', defi) for defi in shortcut_definitions]
        MAX_PARAM_NUMBER = max(len(s) for s in shortcut_param_type)
        # ic(shortcut_param_type)
        match fn:
            # -------------------------------------------- main.c ------------------------------------------------
            case 'main.c':
                code = rf"""
#include "serial_order.h"

int main()
{{
    {self.data['initial','coding']}
    
    while(1)
    {{
        identify_order();
        {self.data['delay_ms']}(200);
    }}
    return 0;
}}"""[1:]
            # -------------------------------------------- func.h ------------------------------------------------
            case 'serial_order.h':
                code = rf"""
#ifndef __SERIAL_ORDER_H__
#define __SERIAL_ORDER_H__

#include <string.h>
{CHAR_N.join(f'#include "{h}"' for h in self.data['initial','includes'])}

#define IS_SERIAL_DEBUGGING SERIAL_NOT_DEBUG // SERIAL_DEBUGGING // 是否正在调试串口

// 仅在IS_SERIAL_DEBUGGING==1才生效
#define debug_println(_Format, ...)                  \
    {{                                                \
        if (IS_SERIAL_DEBUGGING == SERIAL_DEBUGGING) \
        {{                                            \
            if (_Format[0] != '\0')                  \
            {{                                        \
                printf("[debug] ");                  \
                printf(_Format, ##__VA_ARGS__);      \
            }}                                        \
            printf("\n");                            \
        }}                                            \
    }}

#define SERIAL_READBUFF_SIZE 10 // 串口读取缓冲
#define SERIAL_SENDBUFF_SIZE 50 // 串口输出缓冲

// @brief 串口发送字符串
// @param string_ 要发送的字符串
#define serial_putstr(string_) wireless_uart_send_buff((char *)string_, strlen(string_));

// @brief sprintf函数
// @note 因为缓冲有限，替换关键字前先检测长度是否超出限制
#define serial_sprintf(_Dest, _Format, ...)     \
    if (strlen(_Format) > SERIAL_SENDBUFF_SIZE) \
    {{                                           \
        serial_putstr("[Send Buff Burst]: ");   \
        serial_putstr(_Format);                 \
        serial_putstr("\n");                    \
    }}                                           \
    else                                        \
    {{                                           \
        sprintf(_Dest, _Format, ##__VA_ARGS__); \
    }}
    
// @brief 通过串口向主机发送信息
// @note 使用方法和printf函数相同，但输出从MCU指向主机
#define serial_printf(_Format, ...)                         \
    serial_sprintf(VAR_print_buff, _Format, ##__VA_ARGS__); \
    serial_putstr(VAR_print_buff);

// 统一定义变量名称
{''.join((f'#define DEF_{alias.ljust(max_len," ")} {definition.split(" ")[-1].replace(";","")}{CHAR_N}' 
    for alias,definition in zip(aliases,definitions)))}
// 调试信息标志
enum debug_flag
{{
    SERIAL_NOT_DEBUG = 0, // 不在调试
    SERIAL_DEBUGGING = 1, // 正在调试
}};

// 快捷指令枚举
enum shortcut
{{
    SC_None = -1,        // 没有匹配到指令时的缺省值
    SC_SetParameterValue // 设置全局参数值得快捷指令
}};

// 可供调用的全局参数枚举
enum global_param
{{
    PM_ABC, // ABC的title
    PM_DEF  // DEF的title
}};

// 用于存储不同类型的参数值，需要某种类型就调用对应的类型
union type_param
{{
    char char_;
    int int_;
    float float_;
}};

/// @brief 获取字符在字符串中的索引
/// @param src 字符串
/// @param tar 字符
int strIndex(const char *src, const char tar);

/// @brief 接管串口收发
void manage_serial_port(void);

/// @brief 处理收发信息
/// @param uart_buff 新的字符串数组的头指针
/// @param uart_len 字符串的长度
/// @return 匹配到的指令类型
enum shortcut process_information(const char *uart_buff, const int uart_len);

/// @brief 设置全局参数的值
/// @param param 参数索引枚举
/// @param value 设置的参数值
void SetParameterValue(enum global_param param, float value); // 设置全局参数的数值

extern char VAR_print_buff[SERIAL_SENDBUFF_SIZE]; // 重定向输出缓冲区
extern union type_param {', '.join(f"TPp{i}" for i in range(MAX_PARAM_NUMBER))};               // 存储命令的参数

{''.join((f'extern {extern}{CHAR_N}' for extern in externs))}
#endif"""[1:]
            # -------------------------------------------- func.c ------------------------------------------------
            case 'serial_order.c':
                code = rf"""
#include "serial_order.h"

char VAR_print_buff[SERIAL_SENDBUFF_SIZE];
union type_param {', '.join(f"TPp{i}" for i in range(MAX_PARAM_NUMBER))};

// 暂时 只进行匹配单个字符，后续再添加kmp算法
int strIndex(const char *src, const char tar)
{{
    int i, find = 0, len = (int)strlen(src);
    for (i = 0; i < len; i++)
    {{
        if (src[i] == tar)
        {{
            find = 1;
            break;
        }}
    }}
    if (!find)
    {{
        i = -1;
    }}
    return i;
}}

void SetParameterValue(enum global_param param, float value)
{{
    switch (param)
    {{
    {''.join(f'''case PM_{alias}: 
        DEF_{alias} = value; serial_printf("SET {alias}=%g{CHAR_N_}", DEF_{alias}); break;
    ''' for alias in aliases)}default:
        serial_printf("[Warn] Unknow param id=[%d]\n", param); break;
    }}
}}

enum shortcut process_information(const char *uart_buff, const int uart_len)
{{
    // 这个static声明是必要的，其他的static声明是非必要的。
    static char match_buff[100] = "START"; // 静态存储缓冲
    static int buff_len;                   // 缓冲字符串的长度
    static int i, index;                   // 无特殊含义
    enum shortcut ot = SC_None;            // 指令类型

    buff_len = (int)strlen(match_buff);
    
    debug_println("raw & new\t:\"%s\",\"%s\"", match_buff, uart_buff);

    if (buff_len + uart_len >= 100)
    {{
        serial_putstr("[warnning] buff was burst!");
        serial_putstr((const u8 *)match_buff);
        serial_putstr(" | ");
        serial_putstr((const u8 *)uart_buff);
    }}

    // 拼接字符串
    for (i = 0; i < uart_len; i++)
    {{
        match_buff[buff_len + i] = uart_buff[i];
    }}
    match_buff[buff_len + uart_len] = '\0';
    debug_println("joint\t:\"%s\"", match_buff);

    // 如果存在']'才能进行完整的匹配
    index = strIndex(match_buff, ']');
    if (index >= 0 && match_buff[index] == ']')
    {{
        // 匹配预处理，确保第一个字符是'['
        index = strIndex(match_buff, '[');
        if (index > 0)
        {{ // 整体平移
            buff_len = (int)strlen(match_buff);
            for (i = 0; i < buff_len - index; i++)
            {{
                match_buff[i] = match_buff[i + index];
            }}
            match_buff[buff_len - index] = '\0';
        }}

        // 匹配字符串[如果可以匹配]
        if (index >= 0)
        {{ // 若存在'['字符，才进行匹配
            
            sscanf(match_buff, "[%d:", &ot); // 匹配命令类型
            
            switch (ot) // 根据类型执行不同的函数
            {{
            {f'{CHAR_N}'.join(f'''
            case SC_{sc["alias"]}:
                {'sscanf(match_buff, "[%d:'+",".join(replace_type(s) for s in  spts)+ ']", &ot, '
                +", ".join(f"&TPp{spts.index(s)}.{s}_" for s in  spts)+');// 获取参数值' if len(spts) > 0 else '// 无需获取参数值'}
                {sfn}({", ".join(f"TPp{spts.index(s)}.{s}_" for s in  spts)}); // 执行对应事件
                break;''' for sc,sfn,spts in zip(self.data['shortcut'],shortcut_function_name,shortcut_param_type))}
                
            default: // 匹配失败
                debug_println("match None");
                serial_putstr("#");
                ot = SC_None;
                break;
            }}

            // 裁剪字符串[如果匹配成功]
            if (ot != SC_None)
            {{
                buff_len = (int)strlen(match_buff);
                index = strIndex(match_buff, ']') + 1;
                for (i = 0; i < buff_len - index; i++)
                {{
                    match_buff[i] = match_buff[i + index];
                }}
                match_buff[buff_len - index] = '\0';
                //DEF_printf("After-cut\t:\"%s\"\n", match_buff);
            }}
        }}
    }}
    return ot;
}}

void manage_serial_port(void)
{{
    static char VAR_read_buff[SERIAL_READBUFF_SIZE];
    static int VAR_len;
    static enum shortcut VAR_sc;

    VAR_len = wireless_uart_read_buff(VAR_read_buff, SERIAL_READBUFF_SIZE - 1);
    VAR_read_buff[VAR_len] = '\0';

    debug_println("read: \"%s\", len: %d", VAR_read_buff, VAR_len);

    if (SC_None == process_information(VAR_read_buff, VAR_len))
    {{
        serial_putstr(".");
    }}
}}"""[1:]
            case _:
                raise ValueError(f'{fn}未被实现')
        return code
