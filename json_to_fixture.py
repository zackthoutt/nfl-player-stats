import argparse
import json

def json_to_fixture(input_file, app, model, primary_key, output_file):
    with open(input_file, 'r') as f:
        json_data = json.load(f)

    fixture = []
    for instance in json_data:
        new_data = dict()
        new_data['model'] = '{}.{}'.format(app, model.lower())
        new_data['pk'] = instance[primary_key]
        new_data['fields'] = instance
        fixture.append(new_data)

    with open(output_file, 'w') as f:
        json.dump(fixture, f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Input file')
    parser.add_argument('app', help='Name of django app')
    parser.add_argument('model', help='Name of django model')
    parser.add_argument('primary_key', help='Model field containing primary_key')
    parser.add_argument('output', help='Output file')
    args = parser.parse_args()

    json_to_fixture(args.input, args.app, args.model, args.primary_key,
            args.output)
