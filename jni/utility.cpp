//"${JAVA_HOME}/include"
//"${JAVA_HOME}/include/win32"
#include <stdio.h>
#include <cstring>

#include "../std/utility.h"

#include "../jni/java.h"
#include "../jni/keras.h"

#pragma GCC diagnostic ignored "-Wstrict-aliasing"

extern "C" {

jlongArray JNICALL Java_org_dll_Native_double2long(JNIEnv *env, jobject obj,
		jdoubleArray doubleArray) {
	JArray<double> doubleVector(env, doubleArray);
	using pointer = long long *;

	auto _M_start = doubleVector.ptr;
	auto _M_finish = doubleVector.ptr + doubleVector.length();
	auto _M_end_of_storage = _M_finish;

	struct {
		pointer _M_start;
		pointer _M_finish;
		pointer _M_end_of_storage;
	} __struct{(pointer)_M_start, (pointer)_M_finish, (pointer)_M_end_of_storage};

	static_assert(sizeof (long long) == sizeof (double), "long long and double must have same sizes");
	return Object(env, *(vector<long long>*)&__struct);
}

jdoubleArray JNICALL Java_org_dll_Native_long2double(JNIEnv *env, jobject obj,
		jlongArray longArray) {
	JArray<long long> longVector(env, longArray);
	using pointer = double *;

	auto _M_start = longVector.ptr;
	auto _M_finish = longVector.ptr + longVector.length();
	auto _M_end_of_storage = _M_finish;

	struct {
		pointer _M_start;
		pointer _M_finish;
		pointer _M_end_of_storage;
	} __struct{(pointer)_M_start, (pointer)_M_finish, (pointer)_M_end_of_storage};

	static_assert(sizeof (long long) == sizeof (double), "long and double must have same sizes");
	return Object(env, *(vector<double>*)&__struct);
}

}
