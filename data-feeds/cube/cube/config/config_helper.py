import configparser, os

conf = configparser.RawConfigParser()
conf.read('cube/config/settings.cnf')


def get_config(key):
    env = os.getenv('ENVIROMENT', 'DEFAULT')
    print(f'the env is------> {env}')
    result = conf.get(env, key)
    return result
