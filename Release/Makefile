target = eigen

artifact = $(target).dll

GCC = g++ -DNDEBUG -Wall -std=c++17 -fPIC -fopenmp -mavx -mfma
#CMD = -c -fmessage-length=0 -O3 -MMD -MP -MF $(@:%.o=%.d) -MT $@ -o $@ $<
CMD = -c -fmessage-length=0 -O3 -MMD -MP -MT $@ -o $@ $<

SHELL =cmd.exe#this macro is necessary to run $(shell ...) and there should be not spaces left behind!

c_src = $(wildcard ../src/*/*.c)
#$(info $(c_src))

cpp_src = $(wildcard ../src/*/*.cpp ../src/*/*/*.cpp ../src/*/*/*/*.cpp)
#$(info $(cpp_src))

cc_src = $(wildcard ../src/*/*.cc ../src/*/*/*.cc)
#$(info $(cc_src))

asm_src = $(wildcard ../src/*/*.asm)
#$(info $(asm_src))

obj = $(c_src:%.c=%.o) $(cpp_src:%.cpp=%.o) $(cc_src:%.cc=%.o) $(asm_src:%.asm=%.o)
obj := $(foreach file,$(obj),$(subst ../,,$(file)))
$(info $(obj))

$(foreach file,$(sort $(dir $(obj))),$(if $(wildcard $(file)),,$(shell mkdir $(subst /,\,$(file)))))

$(artifact): src/main.o $(obj)
	$(GCC) -shared -o $@ $^

#target must be the first command to execute, so the include directive should follow it!
#so far there are four layers of dependency files
-include $(wildcard src/*.d) $(wildcard src/*/*.d) $(wildcard src/*/*/*.d) $(wildcard src/*/*/*/*.d)

$(target).exe: src/main.o $(obj)
	$(GCC) -o $@ $^

src/jni/%.o: ../src/jni/%.cpp
	$(GCC) -I"$(JAVA_HOME)/include" -I"$(JAVA_HOME)/include/win32" $(CMD)	
	
src/%.o: ../src/%.cpp
	$(GCC) $(CMD)

src/%.o: ../src/%.cc
	$(GCC) $(CMD)

src/%.o: ../src/%.c
	gcc -DNDEBUG -w -std=c99 -fPIC $(CMD)
	        
src/%.o: ../src/%.asm
	as -o $@ $<

clean:
	-rd /s /q src

install: $(artifact) 
	@echo "install $(artifact) to destination ..\\..\\jetty\\src\\main\\resources\\lib\\static\\Windows\\amd64"	
	xcopy $(artifact) ..\..\jetty\src\main\resources\lib\static\Windows\amd64 /Y
	xcopy $(artifact) ..\..\jetty\target\classes\lib\static\Windows\amd64 /Y
	@echo "install $(artifact) to destination ..\\..\\..\\gitlab\\eigen\\Release"	
	xcopy $(artifact) ..\..\..\gitlab\eigen\Release /Y

test: $(target).exe
	./$(target).exe ../../
	@echo "finish testing $(target)!"	
