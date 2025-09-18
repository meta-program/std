//"${JAVA_HOME}/include"
//"${JAVA_HOME}/include/win32"
#include <stdio.h>
#include <cstring>

#include "../ahocorasick/WordSegmenter.h"
#include "../ahocorasick/NERTagger.h"
#include "java.h"

extern "C" {

jobjectArray JNICALL Java_org_dll_cn_Native_segment(JNIEnv *env, jobject obj,
		jstring text) {
	String s = JString(env, text);
	return Object(env, WordSegmenter::instance().segment(s));
}

jobjectArray JNICALL Java_org_dll_cn_Native_split(JNIEnv *env, jobject obj,
		jstring text) {
	String s = JString(env, text);
	return Object(env, WordSegmenter::instance().split(s));
}

//inputs: String [] text;
//ouputs: String [][] segment;

jobjectArray JNICALL Java_org_dll_cn_Native_segments(JNIEnv *env, jobject _,
		jobjectArray text) {
	return Object(env, WordSegmenter::instance().segment(JArray<String>(env, text)));
}
//inputs: String [][] text;
//ouputs: String [][][] segment;
jobjectArray JNICALL Java_org_dll_cn_Native_segmentss(JNIEnv *env, jobject _,
		jobjectArray text) {
	return Object(env,
			WordSegmenter::instance().segment(JArray<vector<String>>(env, text)));
}

jintArray JNICALL Java_org_dll_en_Native_getBase(JNIEnv *env, jobject _) {
	return Object(env,
			NERTagger::instance_en().dat.getBase());
}

jintArray JNICALL Java_org_dll_en_Native_getCheck(JNIEnv *env, jobject _) {
	return Object(env,
			NERTagger::instance_en().dat.getCheck());
}

jintArray JNICALL Java_org_dll_en_Native_getFailure(JNIEnv *env, jobject _) {
	return Object(env,
			NERTagger::instance_en().dat.getFailure());
}

jintArray JNICALL Java_org_dll_en_Native_getValues(JNIEnv *env, jobject _) {
	auto arr = NERTagger::instance_en().dat.getValues();
	vector<int> labels(arr.size());
	for (int i = 0; i< arr.size(); ++i){
		labels[i] = arr[i].label;
	}

	return Object(env, labels);
}

jintArray JNICALL Java_org_dll_en_Native_getCharLength(JNIEnv *env, jobject _) {
	return Object(env,
			NERTagger::instance_en().dat.getCharLength());
}

jobjectArray JNICALL Java_org_dll_en_Native_getEmit(JNIEnv *env, jobject _) {
	return Object(env,
			NERTagger::instance_en().dat.getEmit());
}

jobjectArray JNICALL Java_org_dll_en_Native_getKeys(JNIEnv *env, jobject _) {
	return Object(env,
			NERTagger::instance_en().dat.getKeys());
}
}

//https://linux.thai.net/~thep/datrie/datrie.html
//https://github.com/komiya-atsushi/darts-java
//https://www.hankcs.com/program/algorithm/aho-corasick-double-array-trie.html
