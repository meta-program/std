//"${JAVA_HOME}/include"
//"${JAVA_HOME}/include/win32"
//#include "../java/lang/Character.h"
#include "java.h"

extern "C" {
jint JNICALL Java_org_dll_Native_getType(JNIEnv *env, jobject obj,
		jint jInteger) {
	return 0;
//	return Character::getType((int)jInteger);
}
}
