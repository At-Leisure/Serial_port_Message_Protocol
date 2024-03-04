from zyf.console.config import Config


a = Config()
a.load('./data/one.yaml')
# a.dump('./temp/dump.yaml')


print(a['initial','coding'])