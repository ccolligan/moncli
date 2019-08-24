import json
from enum import Enum 


def create_field(name: str, *argv, **kwargs):

    return GraphQLField(name, *argv, **kwargs)


def create_query(name: str, *argv, **kwargs):
    
    return GraphQLOperation(OperationType.QUERY, name, *argv, **kwargs)


def create_mutation(name: str, *argv, **kwargs):
    
    return GraphQLOperation(OperationType.MUTATION, name, *argv, **kwargs)


class OperationType(Enum):
    QUERY = 1
    MUTATION = 2


class GraphQLNode():

    def __init__(self, name: str):

        self.name: str = name
        self.arguments: dict = {}


    def format_body(self):
        pass


    def format_arguments(self, body: str):

        formatted_args = ', '.join(['{}:{}'.format(key, value) for key, value in self.arguments.items()])
        return '{} ({})'.format(body, formatted_args)


class GraphQLField(GraphQLNode):

    def __init__(self, name: str, *argv, **kwargs):
        super(GraphQLField, self).__init__(name)
        self.__children: dict = {}
        
        self.add_fields(*argv)
        self.add_arguments(**kwargs)


    def add_fields(self, *argv):

        for field in argv:

            if field == None or field == '':
                continue
            
            if type(field) is str:

                field_split = field.split('.')
                existing_field = self.get_field(field_split[0])

                # Add the new fields to the existing field
                if existing_field != None:
                    existing_field.add_fields('.'.join(field_split[1:]))
                    continue

                new_field = GraphQLField(field_split[0])
                new_field.add_fields('.'.join(field_split[1:]))
                self.__children.__setitem__(new_field.name, new_field)

            elif type(field) is GraphQLField:
                self.__children.__setitem__(field.name, field)


    def add_arguments(self, **kwargs):

        for key, value in kwargs.items():

            if type(value) is str:
                self.arguments.__setitem__(key, '"{}"'.format(value))

            elif type(value) is dict:
                # Double the dump to get json arguments to work...
                self.arguments.__setitem__(key, json.dumps(json.dumps(value)))

            elif isinstance(value, Enum):
                self.arguments.__setitem__(key, value.name)

            else:
                self.arguments.__setitem__(key, value)


    def get_field(self, path: str):

        split_path = path.split('.')
        child_name = split_path[0]
        
        if not self.__children.__contains__(child_name):
            return None

        node: GraphQLField = self.__children.get(child_name)
        remaining_path = split_path[1:]

        if (len(remaining_path) == 0):
            return node

        return node.get_field('.'.join(remaining_path))


    def format_body(self):

        body: str = self.name

        if len(self.arguments) > 0:
            body = self.format_arguments(body)

        if len(self.__children) > 0:
            body = self.format_children(body)

        return body

    
    def format_children(self, body: str):

        formatted_children = ', '.join([child.format_body() for child in self.__children.values()])
        return '{} {{ {} }}'.format(body, formatted_children)


class GraphQLOperation(GraphQLField):

    def __init__(self, action_type: OperationType, name: str, *argv, **kwargs):

        self.action_type = action_type.name.lower()
        super(GraphQLOperation, self).__init__(name, *argv, **kwargs)
        self.query_variables: dict = {}


    def add_query_variable(self, key: str, value):

        self.query_variables.__setitem__(key, value)  


    def format_body(self):

        body: str = self.name

        if len(self.arguments) > 0:
            body = self.format_arguments(body)

        body = self.format_children(body)

        body = '{} {{ {} }}'.format(self.action_type, body)

        return body
    