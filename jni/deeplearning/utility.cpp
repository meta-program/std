//"${JAVA_HOME}/include"
//"${JAVA_HOME}/include/win32"
#include "utility.h"

extern "C" {

void JNICALL Java_org_dll_Native_initializeWorkingDirectory(JNIEnv *env,
		jobject obj, jstring pwd) {
	Timer timer(__PRETTY_FUNCTION__);
	void initialize_working_directory(const char *_workingDirectory);
	initialize_working_directory(CString(env, pwd).ptr);
}

jdouble JNICALL Java_org_dll_Native_relu(JNIEnv *env, jobject obj,
		jdouble rcx) {
	return relu(rcx);
}

//jint JNICALL Java_org_dll_Native_gcdint(JNIEnv *env, jobject obj, jint rcx,
//		jint rdx) {
//	return gcd_int(rcx, rdx);
//}

//jlong JNICALL Java_org_dll_Native_gcdlong(JNIEnv *env, jobject obj, jlong rcx,
//		jlong rdx) {
//	return gcd_long(rcx, rdx);
//}

jint JNICALL Java_org_dll_Native_gcdinttemplate(JNIEnv *env, jobject obj,
		jint rcx, jint rdx) {
	return gcd(rcx, rdx);
}

}

jintArray JNICALL Java_org_dll_Native_syntacticBiaffineParser(JNIEnv *env,
		jobjectArray jtext, jintArray jpos_tags,
		SyntacticBiaffineParser &model) {
//	Timer timer(__PRETTY_FUNCTION__);
	vector<vector<String>> text = JArray<vector<String>>(env, jtext);

	JArray<int> indicesJava(env, jpos_tags);
	vector<int> headsCPP = indicesJava;
	const auto &head_indices = model(text, headsCPP);
//	print(head_indices);

	indicesJava = head_indices;
	return jpos_tags;
}

jintArray JNICALL Java_org_dll_Native_paragraphBoundaryTagger(JNIEnv *env,
		jobjectArray jtext, jintArray jTrait, ParagraphBoundaryTagger &model) {
//	Timer timer(__PRETTY_FUNCTION__);
	vector<String> text = JArray<String>(env, jtext);

	VectorI trait_ids = JArray<int>(env, jTrait);
//	print(text);
//	print(trait_ids);
	return Object(env, model(text, trait_ids));
}
