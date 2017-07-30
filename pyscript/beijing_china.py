"""
author : 赵荣欣
date   : 2017-07-11
mail   ; agoagoimy@163.com
desc   : 加载 OSM 数据集.
"""
import sys
sys.path.append('../conf')
import conf

import xml.etree.ElementTree as ET
import json
from functools import reduce
from odo import resource
from odo import discover
from odo import odo


#SAMPLE_FILE = "../data/beijing_china.osm"
SAMPLE_FILE = "../data/sample2.osm"



def main():
	context = load_in_memory(SAMPLE_FILE)
	save_as_json_file(context, '../data/context.json')
	save_as_csv_file(context)
	sync_all_from_csv_to_sqlite(context)


def sync_all_from_csv_to_sqlite(context):
	for item, group in context.items():
		sync_from_csv_to_sqlite('../data/%s.csv' % item,
								'sqlite:////Users/zrx/git/beijing_china.osm/osm_db/osm.db::%s' % item)
		children = list(map(lambda x: x.get('children'), group))
		if len(children) > 0:
			first = children[0]
		else:
			continue
		_types = first.keys()
		for _type in _types:
			children_group = list(reduce(lambda a, b: a + b, list(map(lambda x: x.get(_type), children))))
			if len(children_group) > 0:
				sync_from_csv_to_sqlite('../data/%s_%s.csv' % (item, _type),
										'sqlite:////Users/zrx/git/beijing_china.osm/osm_db/osm.db::%s_%s' % (
										item, _type))
			else:
				continue


def sync_from_csv_to_sqlite(csv_path, sqlite_uri):
	dshape = discover(resource(csv_path))
	odo(csv_path, sqlite_uri, dshape = dshape)


def save_as_json_file(context, path):
	"""
	    @ _desc_		: save context as json file.
	    @ context [Dict]: a context variable.
	    @ path [Str]    : a local system path where to save json file.
	"""
	json.dump(context, open(path , 'w'))


def save_as_csv_file(context):
	"""
		@ _desc_		: save context as csv file.
		@ context [Dict]: a context variable.
		@ path [Str]    : a local system path where to save csv file.
	"""
	for item, group in context.items():
		with open('../data/%s.csv' % item, 'w', encoding='utf-8') as file:
			if len(group) > 0:
				first = group[0]
			else:
				continue
			columns = first.get('attrib').keys()
			file.write(','.join(columns) + '\n')
			rows = list(map(lambda x: extract_attrib(x.get('attrib'), columns), group))
			for row in rows:
				file.write(','.join(row) + '\n')
		children = list(map(lambda x: x.get('children'), group))
		if len(children) > 0:
			first = children[0]
		else:
			continue
		_types = first.keys()
		for _type in _types:
			children_group = list(reduce(lambda a, b: a + b, list(map(lambda x: x.get(_type), children))))
			if len(children_group) > 0:
				first = children_group[0]
			else:
				continue
			columns = first.keys()
			with open('../data/%s_%s.csv' %(item, _type), 'w', encoding='utf-8') as file:
				file.write(','.join(columns) + '\n')
				rows = list(map(lambda x: extract_attrib(x, columns), children_group))
				for row in rows:
					row = list(map(lambda x: str(x), row))
					file.write(','.join(row) + '\n')


def extract_attrib(attrib, columns):
	result = []
	for col in columns:
		result.append(attrib.get(col))
	return  result


def load_in_memory(path):
	data = {
		'node': [],
		'way' : [],
		'relation': []
	}
	for event, elem in ET.iterparse(path):
		_children = elem.getchildren()
		_type = elem.tag
		_tags = []
		_nds = []
		_members = []
		_attrib = elem.attrib
		if _children:
			_parent_id = _attrib.get('id', '')
			_counter = 0
			for _child in _children:
				_child_attr = _child.attrib
				if _child.tag == 'tag':
					_tag_ksplit = _child_attr.get('k', '').split(':')
					if len(_tag_ksplit) == 2:
						_tag_key = _tag_ksplit[1]
						_tag_type = _tag_ksplit[0]
					else:
						_tag_key = _tag_ksplit[0]
						_tag_type = 'regular'
					if ',' in _child_attr.get('v'):
						_tag_value = _child_attr.get('v', '').replace(',', '-')
					else:
						_tag_value = _child_attr.get('v', '')
					_tags.append({
						'id': _parent_id,
						'key': _tag_key,
						'value': _tag_value,
						'type': _tag_type
					})
				if _child.tag == 'nd':
					_nd_ref = _child_attr.get('ref', '')
					_nd_position = _counter
					_counter += 1
					_nds.append({
						'id': _parent_id,
						'node_id': _nd_ref,
						'position': _nd_position
					})
				if _child.tag == 'member':
					_member_ref = _child_attr.get('ref', '')
					_member_role = _child_attr.get('role', '')
					_member_type = _child_attr.get('type', '')
					_member_position = _counter
					_counter += 1
					_members.append({
						'id': _parent_id,
						'node_id': _member_ref,
						'role': _member_role,
						'type': _member_type,
						'position': _member_position
					})
		if _type in ['node', 'way', 'relation']:
			data[_type].append({
				'attrib': _attrib,
				'children':{
					'tag': _tags,
					'nd' : _nds,
					'member': _members
				}
			})
	return data

if __name__ == '__main__':
	main()