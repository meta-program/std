//"${JAVA_HOME}/include"
//"${JAVA_HOME}/include/win32"
#include "../jni/java.h"
#include "../keras/matrix.h"

#include <stdio.h>
#include <cstring>

#include <iostream>

CString::CString(JNIEnv *env, jstring str) :
		env(env), str(str), ptr(env->GetStringUTFChars(str, nullptr)) {
}

CString::operator string() const {
	return string(ptr);
}

bool CString::operator !() const {
	return !ptr;
}

int CString::length() const {
	return ::strlen(ptr);
}

CString::~CString() {
	env->ReleaseStringUTFChars(str, ptr);
}

JString::JString(JNIEnv *env, jstring str) :
		env(env), str(str), ptr(env->GetStringChars(str, nullptr)) {
}

JString::operator String() const {
	return String(ptr, ptr + this->length());
}

bool JString::operator !() const {
	return !ptr;
}

int JString::length() const {
	return env->GetStringLength(str);
}

JString::~JString() {
	env->ReleaseStringChars(str, ptr);
}

JArray<bool>::JArray(JNIEnv *env, jarray arr) :
		env(env), arr(arr), ptr(
				env->GetBooleanArrayElements(arr, JNI_FALSE)) {
}

JArray<bool>::operator vector<bool>() const {
	return vector<bool>(ptr, ptr + this->length());
}

jboolean JArray<bool>::operator [](size_t i) const {
	return ptr[i];
}

jboolean& JArray<bool>::operator [](size_t i) {
	return ptr[i];
}

bool JArray<bool>::operator !() const {
	return !ptr;
}

jsize JArray<bool>::length() const {
	return env->GetArrayLength(arr);
}

JArray<bool>::~JArray() {
	env->ReleaseBooleanArrayElements(arr, ptr, 0);
}

JArray<BYTE>::JArray(JNIEnv *env, jarray arr) :
		env(env), arr(arr), ptr(env->GetByteArrayElements(arr, JNI_FALSE)) {
}

JArray<BYTE>::operator vector<BYTE>() const {
	return vector<BYTE>(ptr, ptr + this->length());
}

jbyte JArray<BYTE>::operator [](size_t i) const {
	return ptr[i];
}

jbyte& JArray<BYTE>::operator [](size_t i) {
	return ptr[i];
}

bool JArray<BYTE>::operator !() const {
	return !ptr;
}

jsize JArray<BYTE>::length() const {
	return env->GetArrayLength(arr);
}

JArray<BYTE>::~JArray() {
	env->ReleaseByteArrayElements(arr, ptr, 0);
}

JArray<short>::JArray(JNIEnv *env, jarray arr) :
		env(env), arr(arr), ptr(env->GetShortArrayElements(arr, JNI_FALSE)) {
}

JArray<short>::operator vector<short>() const {
	return vector<short>(ptr, ptr + this->length());
}

jshort JArray<short>::operator [](size_t i) const {
	return ptr[i];
}

jshort& JArray<short>::operator [](size_t i) {
	return ptr[i];
}

bool JArray<short>::operator !() const {
	return !ptr;
}

jsize JArray<short>::length() const {
	return env->GetArrayLength(arr);
}

JArray<short>::~JArray() {
	env->ReleaseShortArrayElements(arr, ptr, 0);
}

JArray<char16_t>::JArray(JNIEnv *env, jarray arr) :
		env(env), arr(arr), ptr(env->GetCharArrayElements(arr, JNI_FALSE)) {
}

JArray<char16_t>::operator vector<char16_t>() const {
	return vector<char16_t>(ptr, ptr + this->length());
}

jchar JArray<char16_t>::operator [](size_t i) const {
	return ptr[i];
}

jchar& JArray<char16_t>::operator [](size_t i) {
	return ptr[i];
}

bool JArray<char16_t>::operator !() const {
	return !ptr;
}

jsize JArray<char16_t>::length() const {
	return env->GetArrayLength(arr);
}

JArray<char16_t>::~JArray() {
	env->ReleaseCharArrayElements(arr, ptr, 0);
}

JArray<int>::JArray(JNIEnv *env, jarray arr) :
		env(env),

		arr(arr),

		ptr(env->GetIntArrayElements(arr, JNI_FALSE)),

		length(env->GetArrayLength(arr)) {
}

JArray<int>& JArray<int>::operator =(const vector<int> &rhs) {
	for (int i = 0, size = rhs.size(); i < size; ++i) {
		ptr[i] = rhs[i];
	}
	return *this;
}

JArray<int>::operator vector<int>() const {
	return vector<int>(ptr, ptr + length);
}

jint JArray<int>::operator [](size_t i) const {
	return ptr[i];
}

jint& JArray<int>::operator [](size_t i) {
	return ptr[i];
}

bool JArray<int>::operator !() const {
	return !ptr;
}

JArray<int>::~JArray() {
	env->ReleaseIntArrayElements(arr, ptr, 0);
}

JArray<long long>::JArray(JNIEnv *env, jarray arr) :
		env(env), arr(arr), ptr(env->GetLongArrayElements(arr, JNI_FALSE)) {
}

JArray<long long>::operator vector<long long>() const {
	return vector<long long>(ptr, ptr + this->length());
}

jlong JArray<long long>::operator [](size_t i) const {
	return ptr[i];
}

jlong& JArray<long long>::operator [](size_t i) {
	return ptr[i];
}

bool JArray<long long>::operator !() const {
	return !ptr;
}

jsize JArray<long long>::length() const {
	return env->GetArrayLength(arr);
}

JArray<long long>::~JArray() {
	env->ReleaseLongArrayElements(arr, ptr, 0);
}

JArray<float>::JArray(JNIEnv *env, jarray arr) :
		env(env), arr(arr), ptr(env->GetFloatArrayElements(arr, JNI_FALSE)) {
}

JArray<float>::operator vector<float>() const {
	return vector<float>(ptr, ptr + this->length());
}

jfloat JArray<float>::operator [](size_t i) const {
	return ptr[i];
}

jfloat& JArray<float>::operator [](size_t i) {
	return ptr[i];
}

bool JArray<float>::operator !() const {
	return !ptr;
}

jsize JArray<float>::length() const {
	return env->GetArrayLength(arr);
}

JArray<float>::~JArray() {
	env->ReleaseFloatArrayElements(arr, ptr, 0);
}


JArray<double>::JArray(JNIEnv *env, jarray arr) :
		env(env), arr(arr), ptr(env->GetDoubleArrayElements(arr, JNI_FALSE)) {
}

JArray<double>::operator vector<double>() const {
	return vector<double>(ptr, ptr + this->length());
}

jdouble JArray<double>::operator [](size_t i) const {
	return ptr[i];
}

jdouble& JArray<double>::operator [](size_t i) {
	return ptr[i];
}

bool JArray<double>::operator !() const {
	return !ptr;
}

jsize JArray<double>::length() const {
	return env->GetArrayLength(arr);
}

JArray<double>::~JArray() {
	env->ReleaseDoubleArrayElements(arr, ptr, 0);
}

extern "C" {

void JNICALL Java_org_dll_Native_displayHelloWorld(JNIEnv *env, jobject obj) {
	cout << "Hello world!" << endl;
}

int JNICALL Java_org_dll_Native_main(JNIEnv *env, jobject obj) {
	int main(int argc, char **argv);
	return main(0, 0);
}

jstring JNICALL Java_org_dll_Native_reverse(JNIEnv *env, jobject obj,
		jstring str) {
	String s = JString(env, str);
	size_t length = s.size();
	for (size_t i = 0; i < length / 2; ++i) {
		std::swap(s[i], s[length - 1 - i]); // @suppress("Invalid arguments")
	}

	return Object(env, s);
}

}

jstring Object(JNIEnv *env, const string &s) {
	return env->NewStringUTF(s.data());
}

jstring Object(JNIEnv *env, const String &s) {
	static_assert(sizeof (jchar) == sizeof (char16_t), "jchar and char16_t must have same sizes");
	return env->NewString((const jchar*) s.data(), s.size());
}

jintArray SetIntArrayRegion(JNIEnv *env, jsize size, const jint *array) {
	jintArray obj = env->NewIntArray(size);

	env->SetIntArrayRegion(obj, 0, size, array);

	return obj;
}

jlongArray SetLongArrayRegion(JNIEnv *env, jsize size, const jlong *array) {
	jlongArray obj = env->NewLongArray(size);

	env->SetLongArrayRegion(obj, 0, size, array);

	return obj;
}

jintArray Object(JNIEnv *env, const vector<int> &s) {
	static_assert (sizeof(jint) == sizeof(int), "jint and int must have same sizes");
	return SetIntArrayRegion(env, s.size(), (const jint*) s.data());
}

jlongArray Object(JNIEnv *env, const vector<long long> &s) {
	static_assert (sizeof(jlong) == sizeof(long long), "jlong and long long must have the same sizes");
	return SetLongArrayRegion(env, s.size(), (const jlong*) s.data());
}

jobjectArray Object(JNIEnv *env, const Matrix &A) {
	return Object(env, to_double_vector(A));
}

jfloatArray Object(JNIEnv *env, const vector<float> &s) {
	jsize size = s.size();

	const jfloat *array = s.data();

	jfloatArray obj = env->NewFloatArray(size);

	env->SetFloatArrayRegion(obj, 0, size, array);

	return obj;
}

jdoubleArray Object(JNIEnv *env, const VectorD &s) {
	jsize size = s.size();

	const jdouble *array = s.data();

	jdoubleArray obj = env->NewDoubleArray(size);

	env->SetDoubleArrayRegion(obj, 0, size, array);

	return obj;
}

const char *FindClass<bool>::name = "Z";
const char *FindClass<BYTE>::name = "B";
const char *FindClass<char16_t>::name = "C";
const char *FindClass<short>::name = "S";
const char *FindClass<int>::name = "I";
const char *FindClass<long long>::name = "J";
const char *FindClass<float>::name = "F";
const char *FindClass<double>::name = "D";
const char *FindClass<String>::name = "java/lang/String";
const char *FindClass<string>::name = "java/lang/String";

std::ostream& operator <<(std::ostream &cout, const JArray<int> &v) {
	cout << '[';
	if (!v) {
		cout << v[0];
		for (jsize i = 1; i < v.length; ++i) {
			cout << ", " << v[i];
		}
	}

	cout << ']';
	return cout;
}

void print_primitive_type_size() {
	cout << "sizeof(jchar) = " << sizeof(jchar) << endl;
	cout << "sizeof(jbyte) = " << sizeof(jbyte) << endl;
	cout << "sizeof(jboolean) = " << sizeof(jboolean) << endl;
	cout << "sizeof(jshort) = " << sizeof(jshort) << endl;
	cout << "sizeof(jint) = " << sizeof(jint) << endl;
	cout << "sizeof(jlong) = " << sizeof(jlong) << endl;
	cout << "sizeof(jfloat) = " << sizeof(jfloat) << endl;
	cout << "sizeof(jdouble) = " << sizeof(jdouble) << endl;

	cout << "sizeof(char) = " << sizeof(char) << endl;
	cout << "sizeof(wchar_t) = " << sizeof(wchar_t) << endl;
	cout << "sizeof(short) = " << sizeof(short) << endl;
	cout << "sizeof(int) = " << sizeof(int) << endl;
	cout << "sizeof(long) = " << sizeof(long) << endl;
	cout << "sizeof(long long) = " << sizeof(long long) << endl;

	cout << "sizeof(unsigned char) = " << sizeof(unsigned char) << endl;
//	cout << "sizeof(unsigned wchar_t) = " << sizeof(unsigned wchar_t) << endl;
	cout << "sizeof(unsigned short) = " << sizeof(unsigned short) << endl;
	cout << "sizeof(unsigned int) = " << sizeof(unsigned int) << endl;
	cout << "sizeof(unsigned long) = " << sizeof(unsigned long) << endl;
	cout << "sizeof(unsigned long long) = " << sizeof(unsigned long long)
			<< endl;

	cout << "sizeof(float) = " << sizeof(float) << endl;
	cout << "sizeof(double) = " << sizeof(double) << endl;
	cout << "sizeof(BYTE) = " << sizeof(BYTE) << endl;
	cout << "sizeof(word) = " << sizeof(word) << endl;
	cout << "sizeof(dword) = " << sizeof(dword) << endl;
	cout << "sizeof(qword) = " << sizeof(qword) << endl;
	cout << "sizeof(void*) = " << sizeof(void*) << endl;
}

//https://www.cnblogs.com/nicholas_f/archive/2010/11/30/1892124.html
