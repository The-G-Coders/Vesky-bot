import yaml


class YmlConfig:
    """
    A wrapper for handling yml files
    """

    def __init__(self, filepath: str):
        """
        Initializes this class
        :param filepath: the filepath of the yml file
        :type filepath: str
        """
        self.filepath: str = filepath
        with open(fr'{filepath}', 'r') as file:
            self.data: dict = yaml.load(file, Loader=yaml.FullLoader)

    def save(self):
        """
        Saves the contents of the data field to the yml file
        """
        with open(fr'{self.filepath}', 'w') as file:
            yaml.dump(self.data, file, default_flow_style=False, indent=True)

    def overwrite(self, content: dict):
        """Overwrites the data with the dictionary provided and saves it to the yml file"""
        self.data = content
        with open(fr'{self.filepath}', 'w') as file:
            yaml.dump(content, file, default_flow_style=False, indent=True)

    def get(self, path: str):
        """
        Gets the value associated with the key in the resources variable
        :param path: the path, separated by dots
        :return: the value. If not present, returns None
        """
        temp = self.data
        for i, value in enumerate(path.split('.')):
            temp = temp.get(value)
        return temp


if __name__ == '__main__':
    pass
