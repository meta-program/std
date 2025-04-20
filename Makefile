.PHONY: all clean install rebuild

cpu_count =$(shell cat /proc/cpuinfo | grep processor | wc -l)

$(info cpu_count = $(cpu_count))

make_j :=$(shell echo $(cpu_count) | awk '{if($$1 >= "1") {print "make -j"$$1;} else {print "make";}}')

compile: 
#	git pull
	-mkdir ../../temp
	export TMPDIR=../../temp	
# 	fatal error: error writing to /tmp/ccNr2oBQ.s: No space left on device
		
	$(make_j) -C Linux 

clean:
	make -C Linux clean
	
test: compile
	make -C Linux test

rebuild: clean all
	
install: compile
	make -C Linux install
	@echo "finish installing libeigen.so"