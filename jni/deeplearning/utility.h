//"${JAVA_HOME}/include"
//"${JAVA_HOME}/include/win32"
#include <stdio.h>
#include <cstring>

#include "../../std/utility.h"
#include "../../std/lagacy.h"

#include "../../keras/bert.h"
#include "../../keras/markov/NERTagger.h"

#include "../../keras/classification.h"
#include "../../keras/markov/POSTagger.h"
#include "../../keras/parsers/SyntaxParser.h"
#include <jni.h>
#include "../../jni/java.h"
#include "../../jni/keras.h"
#include "../../keras/parsers/claim/boundary.h"
#include "../../keras/parsers/claim/biaffine.h"
#include "../../keras/parsers/claim/chunking.h"

jintArray JNICALL Java_org_dll_Native_syntacticBiaffineParser(JNIEnv *env, jobjectArray jtext,
		jintArray jpos_tags, SyntacticBiaffineParser &model);

jintArray JNICALL Java_org_dll_Native_paragraphBoundaryTagger(JNIEnv *env,
		jobjectArray jtext, jintArray jTrait, ParagraphBoundaryTagger &model);
