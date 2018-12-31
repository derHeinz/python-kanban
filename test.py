import json

masks = [1,2,4,8,16,32,64,128,256,512]

class Tag(object):
	id= 0
	
	def json(self):
		return {
            'id': self.id,
        }


def calc_tags(number):
	ret = []
	for m in masks:
		val = True
		if (number & m) == 0:
			val = False
		if val:
			t = Tag()
			t.id = m
			ret.append(t)
	return ret
	
#zahl = 1
#print(zahl & masks[0])
#print(zahl & masks[1])

tags = calc_tags(189)
print(len(tags))

val = [tag.json() for tag in tags]

print(json.dumps(val))