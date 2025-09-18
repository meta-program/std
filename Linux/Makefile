target = eigen

artifact = lib$(target).so	

JAVA_HOME = $(shell echo $$JAVA_HOME)
ifeq ($(JAVA_HOME), $(nullstring))
	JAVA_HOME := $(shell ls -l `which java` | awk '{if ($$(NF-1) == "->") {print $$NF;} else{}}')
	JAVA_HOME := $(shell ls -l $(JAVA_HOME) | awk '{if ($$(NF-1) == "->") {print $$NF;} else{}}')
	JAVA_HOME := $(dir $(JAVA_HOME))
	JAVA_HOME := $(shell dirname $(JAVA_HOME))
	JAVA_HOME := $(shell dirname $(JAVA_HOME))
endif
$(info JAVA_HOME = $(JAVA_HOME))

GCC = g++ -DNDEBUG -Wall -std=c++17 -fPIC -fopenmp
#CMD = -c -fmessage-length=0 -O3 -MMD -MP -MF $(@:%.o=%.d) -MT $@ -o $@ $<
CMD = -c -fmessage-length=0 -O3 -MMD -MP -MT $@ -o $@ $<

c_src = $(wildcard ../src/*/*.c)
#$(info $(c_src))

cpp_src = $(wildcard ../src/*.cpp ../src/*/*.cpp ../src/*/*/*.cpp ../src/*/*/*/*.cpp)
$(info $(cpp_src))

cc_src = $(wildcard ../src/*/*.cc ../src/*/*/*.cc)
#$(info $(cc_src))

asm_src = $(wildcard ../src/*/*.asm)
#$(info $(asm_src))

obj = $(cpp_src:%.cpp=%.o) $(cc_src:%.cc=%.o) $(c_src:%.c=%.o) $(asm_src:%.asm=%.o)
obj := $(foreach file,$(obj),$(subst ../,,$(file)))
$(info $(obj))

$(foreach file,$(sort $(dir $(obj))),$(if $(wildcard $(file)),,$(shell mkdir -p $(file))))

$(artifact): $(obj)
	$(GCC) -z noexecstack -shared -o $@ $^

#target must be the first command to execute, so the include directive should follow it!
#so far there are four layers of dependency files
-include $(wildcard src/*.d) $(wildcard src/*/*.d) $(wildcard src/*/*/*.d) $(wildcard src/*/*/*/*.d)

$(target).exe: src/main.o $(obj)
	$(GCC) -o $@ $^ -ldl

src/jni/%.o: ../src/jni/%.cpp
	$(GCC) -I$(JAVA_HOME)/include -I$(JAVA_HOME)/include/linux $(CMD)
	
src/%.o: ../src/%.cpp
	$(GCC) $(CMD)
	
src/%.o: ../src/%.cc
	$(GCC) $(CMD)

src/%.o: ../src/%.c
	gcc -DNDEBUG -w -std=c99 -fPIC $(CMD)
	        
src/%.o: ../src/%.asm
	as --defsym linux=1 -o $@ $<

clean:
	-rm -rf src *.class *.so

%.class: %.java
	@echo "compiling $< to $@"
	javac $<

install: $(artifact) LD_LIBRARY_PATH.class
#	@echo "install $(artifact) to destination LD_LIBRARY_PATH"
#	cp -f $(artifact) $(shell java -classpath ./ LD_LIBRARY_PATH)
	
	-mkdir -p ../../jetty/src/main/resources/lib/static/Linux/amd64
	@echo "install $(artifact) to destination ../../jetty/src/main/resources/lib/static/Linux/amd64"	
	cp $(artifact) ../../jetty/src/main/resources/lib/static/Linux/amd64
	
#	@echo "install $(artifact) to destination ../../neural_claim_parser/claimparser-service/src/main/resources/lib/static/Linux/amd64"	
#	cp $(artifact) ../../neural_claim_parser/claimparser-service/src/main/resources/lib/static/Linux/amd64
	
	-mkdir -p ../../pytext/lib
	@echo "install $(artifact) to destination ../../pytext/lib"	
	cp $(artifact) ../../pytext/lib	

test: $(target).exe	
	./$(target).exe ../../ ../../
	@echo "finish testing $(target).exe!"

# https://blog.csdn.net/qq_42334372/article/details/83037362