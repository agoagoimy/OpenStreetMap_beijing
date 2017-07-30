

# 1. OpenStreetMap Of Beijing

### Map Area

Beijing, China

* https://www.openstreetmap.org/relation/912940#map=8/40.256/116.461
* https://mapzen.com/data/metro-extracts/metro/beijing_china/

The extracted file size is over 190MB, which is still too big to process. We need to generate a smaller sample for testing purpose.

Beijing is the capital city of China, where I live. I thought it might be fun to check it out.

# 2. Problems Encountered in the Map

Based on the code and choose “k = 1000” for a file size about 1/1000th of original file size.I noticed five main problems with the data, which I will discuss in the following order:

* Number of way-tags.
* Error data be imported in database.
* Comma problem in some`"v"`("Bing, 2011-7")
* tag "k" value contains a ":" the characters before the ":" should be set as the tag type and characters after the ":" should be set as the tag key.

#### Number of way-tags

A tag **'way'** is an ordered list of nodes  which normally also has at least one tag or is included within a relation. A way can have between 2 and 2,000 nodes, although it's possible that faulty ways with zero or a single node exist.

So, I checked the number of way-nodes in the table of ways_nodes.

```sql
select id,count(*) 
from ways_nodes 
group by id;
```

and part of result is:

```sql
25895788,3
29178837,7
30803075,5
33803505,5
40745413,2
42491092,2
42941180,31
43977772,5
47691618,6
55334711,12
59174592,4
60110810,3
80899825,64
89375367,4
102404841,2
107011220,2
113814500,5
117091205,49
```

and then I checked the tag 'way' only have one child of 'node':

```sql
select id,count(*) as num 
from ways_nodes 
group by id 
having num = 1;
```

and result is nothing.

So, in my sample data the problems of number of way-tags is not exist.

#### Error data be imported in database

When the data was imported successfully, I found that the database contained the field of "id", "type". "key", "value" like this:

```sql
sqlite> select * from nodes_tags;
id,key,value,type
25248662,admin_level,2,regular
25248662,eo,"Bejĝino",alt_name
25248662,fr,Beijing,alt_name
25248662,is,Peking,alt_name
25248662,sv,Peking,alt_name
25248662,capital,yes,regular
25248662,ADM1,22,gns
```

Have you noticed the first line?

```sql
delete from nodes_tags where id='id';
```

now, table is clean:

```sql
sqlite> select * from nodes_tags;
25248662,admin_level,2,regular
25248662,eo,"Bejĝino",alt_name
25248662,fr,Beijing,alt_name
25248662,is,Peking,alt_name
25248662,sv,Peking,alt_name
25248662,capital,yes,regular
25248662,ADM1,22,gns
```

#### Comma problem in some`"v"`

When I was importing data in ways_tags table, throw a error:

```sql
../data/way_tag.csv:162: expected 4 columns but found 5 - extras ignored
```

So I checked my data in the csv file in 162 lines, I found：

```
source,258088780,regular,Bing,2011-7
```

```html
<way changeset="20176041" id="258088780" timestamp="2014-01-24T12:11:41Z" uid="421504" user="u_kubota" version="1">
		<nd ref="2634999670" />
		<nd ref="2634999671" />
		<nd ref="2634999625" />
		<nd ref="2634999624" />
		<nd ref="2634999670" />
		<tag k="source" v="Bing,2011-7" />
		<tag k="building" v="yes" />
</way>
```

Do you notice this data in the second 'tag'? The value of this tag is "Bing,2011-7", so I correcting them in beijing_china.py using the following function:

```python
if ',' in _child_attr.get('v'):
    _tag_value = _child_attr.get('v', '').replace(',', '-')
else:
    _tag_value = _child_attr.get('v', '')
```

and the csv file is becoming:

```
source,258088780,regular,Bing-2011-7
```

#### tag "k" value contains a ":"

For example:

```html
 <tag k="addr:name" v="Lincoln"/>
```

should be turned into : 

```python
{'id': 12345, 'key': 'name', 'value': 'Lincoln', 'type': 'addr'}
```

If some keys are not include ":" that this type is "regular". So I split them in beijing_china.py using the following function:

```python
if _child.tag == 'tag':
    _tag_ksplit = _child_attr.get('k', '').split(':')
    if len(_tag_ksplit) == 2:
        _tag_key = _tag_ksplit[1]
        _tag_type = _tag_ksplit[0]
    else:
        _tag_key = _tag_ksplit[0]
        _tag_type = 'regular'
```

and part of result is:

```sql
339088654,railway,station,regular
339088654,public_transport,stop_position,regular
700771136,name,"东二旗村",regular
700771136,place,village,regular
700771136,zh_pinyin,"Dong'er Qicun",name
983351383,amenity,bicycle_parking,regular
1037703596,man_made,tower,regular
1230360715,power,tower,regular
1296102340,railway,subway_entrance,regular
1366335070,name,"清河",regular
```

# 3. Data Overview and Additional Ideas

This section contains basic statistics about the dataset, the MongoDB queries used to gather them, and some additional ideas about the data in context.I wrote a reusable code and used the ODO module to import the database automatically.There were a lot of problems and it took a lot of time to solve the problem.

### File sizes

```
beijing_china.osm......... 190.5 MB
osm.db .......... 158 kB
node.csv ............. 70 MB
node_tag.csv ........ 3 MB
way.csv .............. 7.4 MB
way_tag.csv ......... 8.4 MB
way_nd.cv ......... 23.6 MB
```

### Number of nodes

```sql
sqlite> select count(*) from node;
```

857229

### Number of ways

```sql
sqlite> select count(*) from way;
```

127883

### Number of way_node

```sql
sqlite> select count(*) from way_node;
```

1023113

### Number of unique users

```sql
sqlite> select count(distinct(e.uid)) from (select uid from node union ALL select uid from way) e;
```

1830

### Number of buildings

```sql
sqlite> select count(*) from node_tag where key = 'building';
221
sqlite> select count(*) from way_tag where key = 'building';
31779
```

### Top 10 contributing users

```sql
sqlite> SELECT e.user, COUNT(*) as num 
FROM (SELECT user 
      FROM node 
      UNION ALL 
      SELECT user 
      FROM way)e 
GROUP BY e. user
ORDER BY num DESC 
LIMIT 10 ;
```

```
Chen Jia|237890
R438|142355
hanchao|68254
ij_|51900
Алекс Мок|47488
katpatuka|23439
m17design|21595
Esperanza36|18607
nuklearerWintersturm|16462
RationalTangle|13740
```

### Number of users appearing only once (having 1 post)

```sql
qlite> SELECT COUNT(*) 
FROM (SELECT e.user, COUNT(*) as num 
      FROM (SELECT user 
            FROM node 
            UNION ALL 
            SELECT user 
            FROM way) e 
      GROUP BY e.user 
      HAVING num=1)  u;
```

441

### Top building types

```sql
sqlite> select value, count(*) as num 
from node_tag 
where key = 'building' 
group by value 
order by num desc 
limit 10;
```

```
yes|91
apartments|29
residential|29
office|18
school|13
commercial|10
house|10
entrance|4
hotel|4
hospital|3
```

# 4. Additional Ideas

### Improvements

As seen in the query just above, 41% of buildings are just labeled with yes instead of the building type. This sample actually mirrors the overall percentage of all building tags; 41% are labeled yes . The OpenStreetMap
wiki says to only use the yes value "where it is not possible to determine a more specific value."1 I highly doubt that more than 40% of buildings can't be classified with a more specific value. Even getting that percentage down to 20% would be useful for looking at things like city zoning and densities of industrial or residential building types.

# 5. Additional Data Exploration

### Top 10 appearing amenities

```sql
sqlite> SELECT value, COUNT(*) as num 
FROM node_tag 
WHERE key = 'amenity' 
GROUP BY value 
ORDER BY num DESC 
LIMIT 10;
```

```
restaurant|1281
bank|455
toilets|360
fast_food|329
cafe|278
school|161
bar|151
telephone|151
parking|135
atm|114
```

### Most popular cuisines

```sql
sqlite> SELECT node_tag.value, COUNT(*) as num 
FROM node_tag 
JOIN (SELECT DISTINCT(id) 
      FROM node_tag 
      WHERE value='restaurant') i 
ON node_tag.id=i.id 
WHERE node_tag.key='cuisine' 
GROUP BY node_tag.value 
ORDER BY num DESC
LIMIT 10;
```

```
chinese|167
japanese|21
italian|17
pizza;american|15
regional|11
international|10
pizza|9
american|7
asian|7
german|5
```

# 6. Conclusion

OpenStreetMap has a lot of data not only entered by users, but also defined by users in a lot of cases. Auditing one aspect of the dataset at a time, like done above, and fixing errors seems like the best approach. I think if OpenStreetMap developed auditing tools for the community, they could crowd­source the cleaning of their data.


