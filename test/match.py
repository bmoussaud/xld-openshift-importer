import re


def method_name(data):
    print(data)
    pattern = r'(.*)\$({\w*})(.*)'
    matchObj = re.match(pattern, data)
    if matchObj:
        new_data = "{0}{{{1}}}{2}".format(matchObj.group(1), matchObj.group(2), matchObj.group(3))
        print(new_data)
        return new_data


method_name("coolstore-catalog:${APP_VERSION}")
method_name("${IMAGESTREAM_NAMESPACE}")
print('-- done')
