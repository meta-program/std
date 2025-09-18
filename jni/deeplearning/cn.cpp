#include "utility.h"

extern "C" {

jobjectArray JNICALL Java_org_dll_Native_NER(JNIEnv *env, jobject obj,
		jstring _service, jstring _text, jintArray _code) {
	string service = CString(env, _service);
	String text = JString(env, _text);
	JArray<int> code(env, _code);
	cout << "code from java = " << code << endl;

	VectorI arr = code;
	cout << "converted to C++ = " << arr << endl;

	TensorD debug;
	NERTaggerDict::_predict(service, text, arr, debug);
	return Object(env, debug);
}

//inputs: String [] text;
//ouputs: String [][] segment;

jintArray JNICALL Java_org_dll_cn_Native_dep(JNIEnv *env, jobject _,
		jobjectArray seg, jobjectArray pos, jobjectArray dep, jintArray heads) {
	auto &instance = SyntaxParser::instance_cn();
	vector<String> segCPP = JArray<String>(env, seg);
	vector<String> posCPP = JArray<String>(env, pos);

	vector<String> depCPP;
	if (heads == nullptr) {
		heads = Object(env, instance(segCPP, posCPP, depCPP));
	} else {
		JArray<int> headsJava(env, heads);
		vector<int> headsCPP = headsJava;
		instance(segCPP, posCPP, depCPP, headsCPP);
		headsJava = headsCPP;
	}

	JArray<String> depJava(env, dep);
	depJava = depCPP;
	return heads;
}

//inputs: String [] text;
//ouputs: String [][] segment;

//jobjectArray JNICALL Java_org_dll_cn_Native_pos(JNIEnv *env, jobject _,
//		jobjectArray text, jobjectArray pos) {
//	vector<String> segCPP = JArray<String>(env, text);
//
//	auto &instance = POSTagger::instance();
//	if (pos == nullptr)
//		return Object(env, instance.predict(segCPP));
//
//	JArray<String> posJava(env, pos);
//	vector<String> posCPP = posJava;
//
//	print(posCPP);
//
//	instance.predict(segCPP, posCPP);
//
//	posJava = posCPP;
//	return pos;
//}

//jint JNICALL Java_org_dll_cn_Native_keyword(JNIEnv *env, jobject obj,
//		jstring str) {
//	String s = JString(env, str);
//	int index;
//	return ClassifierChar::instance().predict(s, index);
//}

//jintArray JNICALL Java_org_dll_Native_keywordCNs(JNIEnv *env, jobject _,
//		jobjectArray str) {
//	vector<String> ss = JArray<String>(env, str);
//	vector<int> index;
//	return Object(env, ClassifierChar::instance().predict(ss, index));
//}

//jdouble JNICALL Java_org_dll_Native_similarity(JNIEnv *env, jobject obj,
//		jstring x, jstring y) {
//	String s1 = JString(env, x);
//	String s2 = JString(env, y);
//
//	cout << "s1 = " << s1 << endl;
//	cout << "s2 = " << s2 << endl;
//
//	return Pairwise::paraphrase()(s1, s2);
//}

jintArray JNICALL Java_org_dll_cn_Native_paragraphBoundaryTagger(JNIEnv *env,
		jobject obj, jobjectArray jtext, jintArray jpos_tags) {
	//	Timer timer(__PRETTY_FUNCTION__);
	return Java_org_dll_Native_paragraphBoundaryTagger(env, jtext, jpos_tags,
			ParagraphBoundaryTagger::instance_cn());
}

jintArray JNICALL Java_org_dll_Native_ner(JNIEnv *env, jobject obj,
		jstring _service, jstring _text, jintArray _code) {
	string service = CString(env, _service);
	String text = JString(env, _text);
	JArray<int> code(env, _code);

	{
		JArray<BYTE> code(env, 0);
	}
	{
		JArray<bool> code(env, 0);
	}
	{
		JArray<short> code(env, 0);
	}
	{
		JArray<long> code(env, 0);
	}
	{
		JArray<float> code(env, 0);
	}
	{
		JArray<double> code(env, 0);
	}
	{
		JArray<String> code(env, (jobjectArray) 0);
	}
//	cout << "code from java = " << code << endl;

	VectorI arr = code;
//	cout << "converted to C++ = " << arr << endl;

	NERTaggerDict::predict(service, text, arr);
	return Object(env, arr);
}

jintArray JNICALL Java_org_dll_cn_Native_syntacticChunkingTagger(JNIEnv *env,
		jobject obj, jobjectArray jtext) {
//	Timer timer(__PRETTY_FUNCTION__);
	vector<String> text = JArray<String>(env, jtext);
//	print(text)
	return Object(env, SyntacticChunkingTagger::instance_cn()(text));
}

jobjectArray JNICALL Java_org_dll_cn_Native_chunkingDebug(JNIEnv *env,
		jobject obj, jobjectArray jtext) {
//	Timer timer(__PRETTY_FUNCTION__);
	vector<vector<String>> text = JArray<vector<String>>(env, jtext);
//	print(text)
	return Object(env, SyntacticChunkingTagger::instance_cn()(text, true));
}

jintArray JNICALL Java_org_dll_cn_Native_syntacticBiaffineParser(JNIEnv *env,
		jobject obj, jobjectArray jtext, jintArray jpos_tags) {
//	Timer timer(__PRETTY_FUNCTION__);
	return Java_org_dll_Native_syntacticBiaffineParser(env, jtext, jpos_tags,
			SyntacticBiaffineParser::instance_cn());
}
}
