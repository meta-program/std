#include "utility.h"

extern "C" {

jintArray JNICALL Java_org_dll_Native_tokens2idsEN(JNIEnv *env, jobject _,
		jobjectArray text) {
	Timer timer(__PRETTY_FUNCTION__);
	vector<String> ctext = JArray<String>(env, text);
//	print(ctext);
	return Object(env,
			FullTokenizer::instance_en().convert_tokens_to_ids(ctext));

}

jintArray JNICALL Java_org_dll_Native_token2idEN(JNIEnv *env, jobject _,
		jstring text) {
	static const string comma(1, ',');
	std::vector<std::string> pieces;
	String str = JString(env, text);
	auto &tokenizer = FullTokenizer::instance_en();
	auto tokens = tokenizer.tokenize(str);

	auto ids = tokenizer.convert_tokens_to_ids(tokens);

	return Object(env, ids);
}

jobjectArray JNICALL Java_org_dll_Native_tokenizeEN(JNIEnv *env, jobject _,
		jstring text) {
	Timer timer(__PRETTY_FUNCTION__);
	vector<string> pieces;

	auto &tokenizer = FullTokenizer::instance_en();
	String str = JString(env, text);
	auto tokens = tokenizer.tokenize(str);

//	print(pieces);
	return Object(env, tokens);
}

jintArray JNICALL Java_org_dll_en_Native_paragraphBoundaryTagger(JNIEnv *env,
		jobject obj, jobjectArray jtext, jintArray jpos_tags) {
//	Timer timer(__PRETTY_FUNCTION__);
	return Java_org_dll_Native_paragraphBoundaryTagger(env, jtext, jpos_tags,
			ParagraphBoundaryTagger::instance_en());
}

jintArray JNICALL Java_org_dll_en_Native_syntacticBiaffineParser(JNIEnv *env,
		jobject obj, jobjectArray jtext, jintArray jpos_tags) {
//	Timer timer(__PRETTY_FUNCTION__);
	return Java_org_dll_Native_syntacticBiaffineParser(env, jtext, jpos_tags,
			SyntacticBiaffineParser::instance_en());
}

jintArray JNICALL Java_org_dll_en_Native_syntacticChunkingTagger(JNIEnv *env,
		jobject obj, jobjectArray jtext) {
//	Timer timer(__PRETTY_FUNCTION__);
	vector<String> text = JArray<String>(env, jtext);
//	print(text);
	return Object(env, SyntacticChunkingTagger::instance_en()(text));
}

jobjectArray JNICALL Java_org_dll_en_Native_chunkingDebug(JNIEnv *env,
		jobject obj, jobjectArray jtext) {
//	Timer timer(__PRETTY_FUNCTION__);
	vector<vector<String>> text = JArray<vector<String>>(env, jtext);
//	print(text);
	return Object(env, SyntacticChunkingTagger::instance_en()(text, true));
}

jobjectArray JNICALL Java_org_dll_en_Native_sbdDebug(JNIEnv *env, jobject obj,
		jobjectArray jtext) {
	Timer timer(__PRETTY_FUNCTION__);
	vector<String> text = JArray<String>(env, jtext);
	print(text);
	return Object(env, ParagraphBoundaryTagger::instance_en()(text, true));
}

jint JNICALL Java_org_dll_en_Native_keyword(JNIEnv *env, jobject obj,
		jstring str) {
	Timer timer(__PRETTY_FUNCTION__);
	String s = JString(env, str);
	int index;
	return ClassifierWord::instance().predict(s, index);
}

jintArray JNICALL Java_org_dll_Native_keywordENs(JNIEnv *env, jobject _,
		jobjectArray str) {
	Timer timer(__PRETTY_FUNCTION__);
	vector<String> ss = JArray<String>(env, str);

	vector<int> index;
	return Object(env, ClassifierWord::instance().predict(ss, index));
}
}
