class CubeHelper:
    total_segament_size = 100

    def __init__(self):
        """
        初始化生成{total_segament_size}的数组对象
        """
        for i in range(0, self.total_segament_size + 1):
            setattr(self, f'array{str(i)}', [])

    def generate_symbol_array(self):
        """
        根据指定的起始组合代码和结束组合代码，生成组合代码，并将组合代码进行hash取模的结果分配到不同的数组里面
        :return:
        """
        start = 115
        # total = 2082314
        end = 2084391
        for i in range(start, end):
            symbol = "ZH%06d" % i
            index = hash(symbol) % self.total_segament_size
            getattr(self, f'array{str(index)}').append(symbol)
