
import time
import sys
import datetime
# https://note.com/yucco72/n/n11e9be3cf541 (2024/02/26)
# uvicornとlogging
# https://zenn.dev/techflagcorp/articles/8d6327311e1e9f (2024/02/26)

counter = int(sys.argv[1])
print(sys.argv[2] , 'start' , datetime.datetime.now() , counter)
while counter > 0:
	time.sleep(1)
	counter -= 1

print(sys.argv[2] , 'count up' , datetime.datetime.now())
exit(0)
