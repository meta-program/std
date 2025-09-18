#pragma once

#include <jni.h>
#include "../std/utility.h"

struct CString {
	CString(JNIEnv *env, jstring str);

	operator string() const;

	bool operator !() const;

	int length() const;

	~CString();

	JNIEnv *const env;
	const jstring str;
	const char *const ptr;
};

struct JString {
	JString(JNIEnv *env, jstring str) ;

	operator String() const;

	bool operator !() const;

	int length() const;

	~JString();

	JNIEnv *const env;
	const jstring str;
	const jchar *const ptr;
};

template<typename _Ty> struct FindClass {
};

template<typename _Ty>
struct JArray {
	using jarray = jobjectArray;
	JArray(JNIEnv *env, jarray arr) :
			env(env), arr(arr) {
	}

	struct reference {
		reference(JNIEnv *env, jarray arr, jsize index) :
				env(env), arr(arr), index(index) {
		}

		operator jobject() {
			return env->GetObjectArrayElement(arr, index);
		}

		JNIEnv *const env;
		const jarray arr;
		jsize index;

		reference& operator =(const _Ty &value) {
			jobject val = Object(env, value);
			env->SetObjectArrayElement(arr, index, val);
			env->DeleteLocalRef(val);
			return *this;
		}
	};

	JArray& operator =(const vector<_Ty> &rhs) {
		for (int i = 0, size = rhs.size(); i < size; ++i) {
			(*this)[i] = rhs[i];
		}
		return *this;
	}

	operator vector<_Ty>() const {
		int length = this->length();
		vector<_Ty> result(length);

		for (int k = 0; k < length; ++k) {
			result[k] = typename FindClass<_Ty>::JObject(env,
					(typename FindClass<_Ty>::jobject) (jobject) (*this)[k]);
		}

		return result;
	}

	jobject operator [](size_t i) const {
		return env->GetObjectArrayElement(arr, i);
	}

	reference operator [](size_t i) {
		return reference(env, arr, i);
	}

	bool operator !() const {
		return !length();
	}

	jsize length() const {
		return env->GetArrayLength(arr);
	}

	JNIEnv *const env;
	const jarray arr;
};

jstring Object(JNIEnv *env, const string &s);
jstring Object(JNIEnv *env, const String &s);
jbooleanArray Object(JNIEnv *env, const vector<bool> &s);
jcharArray Object(JNIEnv *env, const vector<char> &s);
jbyteArray Object(JNIEnv *env, const vector<BYTE> &s);
jshortArray Object(JNIEnv *env, const vector<short> &s);
jintArray Object(JNIEnv *env, const vector<int> &s);

jfloatArray Object(JNIEnv *env, const vector<float> &s);
jlongArray Object(JNIEnv *env, const vector<long long> &s);


template<>
struct FindClass<bool> {
	static const char *name;
	using jobject = jboolean;
};

template<>
struct JArray<bool> {
	using jarray = jbooleanArray;
	JArray(JNIEnv *env, jarray arr);

	operator vector<bool>() const;

	jboolean operator [](size_t i) const;

	jboolean& operator [](size_t i);

	bool operator !() const;

	jsize length() const;

	~JArray();

	JNIEnv *const env;
	const jarray arr;
	jboolean *const ptr;
};

template<>
struct FindClass<BYTE> {
	static const char *name;
	using jobject = jbyte;
};

template<>
struct JArray<BYTE> {
	using jarray = jbyteArray;
	JArray(JNIEnv *env, jarray arr);

	operator vector<BYTE>() const;

	jbyte operator [](size_t i) const;

	jbyte& operator [](size_t i);

	bool operator !() const;

	jsize length() const;

	~JArray();

	JNIEnv *const env;
	const jarray arr;
	jbyte *const ptr;
};

template<>
struct FindClass<short> {
	static const char *name;
	using jobject = jshort;
};

template<>
struct JArray<short> {
	using jarray = jshortArray ;
	JArray(JNIEnv *env, jarray arr);

	operator vector<short>() const;

	jshort operator [](size_t i) const;

	jshort& operator [](size_t i);

	bool operator !() const;

	jsize length() const;

	~JArray();

	JNIEnv *const env;
	const jarray arr;
	jshort *const ptr;
};

template<>
struct FindClass<char16_t> {
	static const char *name;
	using jobject = jchar;
};

template<>
struct JArray<char16_t> {
	using jarray = jcharArray ;
	JArray(JNIEnv *env, jarray arr);

	operator vector<char16_t>() const;

	jchar operator [](size_t i) const;

	jchar& operator [](size_t i);

	bool operator !() const;

	jsize length() const;

	~JArray();

	JNIEnv *const env;
	const jarray arr;
	jchar *const ptr;
};

template<>
struct FindClass<int> {
	static const char *name;
	using jobject = jint;
};

template<>
struct JArray<int> {
	using jarray = jintArray;
	JArray(JNIEnv *env, jarray arr);

	JArray& operator =(const vector<int> &rhs);

	operator vector<int>() const;

	jint operator [](size_t i) const;

	jint& operator [](size_t i);

	bool operator !() const;

	~JArray();

	JNIEnv *const env;
	const jarray arr;
	jint *const ptr;
	int length;
};

template<>
struct FindClass<long long> {
	static const char *name;
	using jobject = jlong;
};

template<>
struct JArray<long long> {
	using jarray = jlongArray ;
	JArray(JNIEnv *env, jarray arr);

	operator vector<long long>() const;

	jlong operator [](size_t i) const;

	jlong& operator [](size_t i);

	bool operator !() const;

	jsize length() const;

	~JArray();

	JNIEnv *const env;
	const jarray arr;
	jlong *const ptr;
};

template<>
struct FindClass<float> {
	static const char *name;
	using jobject = jfloat;
};

template<>
struct JArray<float> {
	using jarray = jfloatArray;
	JArray(JNIEnv *env, jarray arr);

	operator vector<float>() const;

	jfloat operator [](size_t i) const;

	jfloat& operator [](size_t i);

	bool operator !() const;

	jsize length() const;

	~JArray();

	JNIEnv *const env;
	const jarray arr;
	jfloat *const ptr;
};

template<>
struct FindClass<double> {
	static const char *name;
	using jobject = jdouble;
};

#include "../std/lagacy.h"

template<>
struct JArray<double> {
	using jarray = jdoubleArray ;
	JArray(JNIEnv *env, jarray arr);

	operator vector<double>() const ;

	jdouble operator [](size_t i) const;

	jdouble& operator [](size_t i);

	bool operator !() const;

	jsize length() const;

	~JArray();

	JNIEnv *const env;
	const jarray arr;
	jdouble *const ptr;
};

template<typename _Ty>
struct FindClass<vector<_Ty>> {
	static const char *name;
	using JObject = JArray<_Ty>;
	using jobject = typename JObject::jarray;
};

template<>
struct FindClass<String> {
	static const char *name;
	using jobject = jstring ;
	using JObject = JString ;
};

template<>
struct FindClass<string> {
	static const char *name;
	using jobject = jstring;
	using JObject = CString;
};

#include <string.h>
template<typename _Ty>
const char *FindClass<vector<_Ty>>::name = [](const char *name) -> const char* {
	string left_bracket = "[";
	static string array_name;
	assert(!array_name);

	if ((::strlen(name) == 1 && isupper(name[0])) || name[0] == '[') {
		//for primitive types or //for array of arrays;
		array_name = left_bracket + name;
	} else {
		//[Ljava/lang/String;
		array_name = left_bracket + 'L' + name + ';';
	}
//	cout << "array type for " << name << " = " << array_name << endl;
	return array_name.c_str();
}(FindClass<_Ty>::name);

template<typename _Ty>
jobjectArray Object(JNIEnv *env, const vector<_Ty> &arr) {
	int sz = arr.size();

//	cout << "vector size = " << sz << endl;
//	cout << "classname = " << FindClass<_Ty>::name << endl;
	auto jclass = env->FindClass(FindClass<_Ty>::name);

	auto obj = env->NewObjectArray(sz, jclass, nullptr);

	JArray<_Ty> array(env, obj);
	for (int k = 0; k < sz; ++k) {
		array[k] = arr[k];
	}

	env->DeleteLocalRef(jclass);
	return obj;
}

template<typename _Ty>
jobjectArray Object(JNIEnv *env, const std::forward_list<_Ty> &arr, int size) {

	auto jclass = env->FindClass(FindClass<_Ty>::name);
	auto obj = env->NewObjectArray(size, jclass, nullptr);

	auto iter = arr.begin();

	JArray<_Ty> array(env, obj);
	for (int k = 0; k < size; ++k) {
		array[k] = *iter++;
	}

	env->DeleteLocalRef(jclass);
	return obj;
}

std::ostream& operator <<(std::ostream &cout, const JArray<int> &v);
