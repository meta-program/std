#pragma once

#include <jni.h>
#include "java.h"
#include "../keras/utility.h"
jintArray Object(JNIEnv *env, const VectorI &s);
jobjectArray Object(JNIEnv *env, const Matrix &s);

jdoubleArray Object(JNIEnv *env, const VectorD &s);

template<>
struct FindClass<Vector> {
	static const char *name;
	using JObject = JArray<double>;
	using jobject = typename JObject::jarray;
};

template<>
struct FindClass<Matrix> {
	static const char *name;
	using JObject = JArray<VectorD>;
	using jobject = typename JObject::jarray;
};
