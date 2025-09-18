#include "utility.h"

extern "C" {

jintArray JNICALL Java_org_dll_kr_Native_paragraphBoundaryTagger(JNIEnv *env,
		jobject obj, jobjectArray jtext, jintArray jpos_tags) {
//	Timer timer(__PRETTY_FUNCTION__);
	return Java_org_dll_Native_paragraphBoundaryTagger(env, jtext, jpos_tags,
			ParagraphBoundaryTagger::instance_kr());
}

jintArray JNICALL Java_org_dll_kr_Native_syntacticBiaffineParser(JNIEnv *env,
		jobject obj, jobjectArray jtext, jintArray jpos_tags) {
//	Timer timer(__PRETTY_FUNCTION__);
	return Java_org_dll_Native_syntacticBiaffineParser(env, jtext, jpos_tags,
			SyntacticBiaffineParser::instance_kr());
}

jintArray JNICALL Java_org_dll_kr_Native_syntacticChunkingTagger(JNIEnv *env,
		jobject obj, jobjectArray jtext) {
//	Timer timer(__PRETTY_FUNCTION__);
	vector<String> text = JArray<String>(env, jtext);
//	print(text);
	return Object(env, SyntacticChunkingTagger::instance_kr()(text));
}

}
