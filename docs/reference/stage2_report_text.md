# Stage 2 Report (Level 2, Revised) — extracted text

> **Provenance.** Text extracted from the submitted PDF
> `FAI_PE_Microproject_Stage_2_Report_Revised.pdf` (found at `C:\Users\purvj\Downloads\.pdf\FAI_PE_Microproject_Stage_2_Report_Revised.pdf`, 764,646 bytes) using `pdfplumber`
> page-by-page extraction on 2026-10-08.
>
> - Pages extracted: **15**
> - Extraction produced **32,150** bytes of text
>
> **This is a convenience copy, not the authoritative document.** The submitted PDF remains the
> source of truth. Figures and images are **not** captured — Stage 2 references Figures 1–5, which
> are images in the PDF and are therefore **missing here**. Any claim about a figure's content must
> be checked against the PDF itself.
>
> Extracted for `docs/03_GAP_ANALYSIS.md` and `docs/01_REQUIREMENTS.md` so that the specification is
> greppable and diffable across sessions.

---


---

## PDF page 1
Department of Computer Engineering
Academic Year: 2026-2027
Microproject Report — Level 2
Project Title
“RAG-Based Academic Research Assistant with Citation
Verification”
Team Members:
Rishabh Jain (Prn: 124BTCM1054)
Purv Jain (Prn: 124BTCM1171)
Bhavya Soni (Prn: 124BTCM1215)
Project Guide:
Prof. Priyanka Kharatmol
1

---

## PDF page 2
1. Title Page & Executive Summary
1.1 Project Abstract
This Stage 2 report converts the project idea defined in Level 1 into a concrete, zero-paid-API
implementation plan and a working local prototype. The system accepts academic PDF documents,
validates and extracts page-level text, divides the text into overlapping evidence chunks, indexes
those chunks for retrieval, answers a user query from the retrieved evidence, attaches source
markers, and finally checks whether each cited claim is actually supported by the referenced
evidence. The central design objective is not to produce the most fluent answer at any cost; it is to
make the answer traceable enough that a student can inspect why a statement was produced. The
retrieval-grounded design follows the RAG approach introduced by Lewis et al. and later surveyed
by Gao et al. [1], [2].
The implementation is deliberately local-first. The intended semantic profile uses the all-
MiniLM-L6-v2 sentence-embedding model, Chroma for persistent vector storage, a small local
FLAN-T5 generator, and Streamlit for the user interface. A second offline validation profile uses
TF-IDF retrieval, an in-memory vector store, and extractive grounded generation. This fallback
profile is not a replacement for the semantic profile; it is included so that ingestion, retrieval,
citation formatting, verification, and testing can still be demonstrated on an ordinary laptop even
before optional model weights are downloaded. The selected local components are documented by
their respective maintainers [7]-[11].
For Stage 2 validation, the Level 1 report itself was used as a reproducible input document. The
prototype extracted all 11 pages, produced 28 evidence chunks using the revised chunking policy,
retrieved the correct resource-plan page for a stack-related query, generated source-marked output,
and passed 10 automated tests covering validation, extraction, chunking, retrieval, query handling,
and citation verification. The result is therefore a buildable microproject rather than a report that
depends on paid APIs or hardware unavailable to the team.
1.2 Current Stage Outcomes
 A modular Python project structure has been defined and exercised with a reproducible local
demo.
 PDF validation, page-wise extraction, sentence-aware overlapping chunking, retrieval, grounded
answer construction, and citation verification are implemented as separate modules.
 The design no longer treats LangChain as an LLM. The generator and orchestration
responsibilities are separated explicitly.
2

---

## PDF page 3
 The chunk size has been reduced from the Level 1 proposal so that evidence is not silently
truncated by the MiniLM embedding model.
 No paid API key is required for the proposed final configuration. Model downloads and local
execution are the only external requirements.
 Automated testing currently reports 10/10 passing tests in the validation profile.
1.3 Stage 1 Validation and Corrections
Before writing this report, the Level 1 document was treated as a design proposal rather than as
an unquestionable specification. Several items were technically inconsistent or too strong for a
microproject. Stage 2 keeps the original objective but corrects those points so that the system can be
built and defended during viva.
Table 1: Stage 1 validation issues and Stage 2 corrections
Level 1 issue Stage 2 correction
LangChain is an application/orchestration framework, not the language model itself.
LangChain listed as “LLM” Stage 2 removes it from the LLM slot. The generator is specified separately as a local
FLAN-T5-small option; direct Python orchestration is sufficient for this project. [6]
Level 1 used both units in different sections. Stage 2 standardizes the fallback chunker
500 tokens vs. 500 words to about 180 words with 30-word overlap. This is intentionally below MiniLM’s
practical input limit so evidence is not heavily truncated. [8]
A cosine-similarity score is evidence of semantic relatedness, not proof that a citation
Fixed verification thresholds treated
is factually correct. Stage 2 uses configurable thresholds and labels the middle band
as proof
“Needs Review”. Thresholds must be calibrated on a manually labelled test set.
Low similarity can also result from paraphrasing or extraction noise. Stage 2 uses
“Hallucinated” used for every low
“Unsupported” for weak/no evidence and reserves the word hallucination for
score
interpretation during evaluation.
The maintained package name is now pypdf. Stage 2 uses pypdf first and pdfplumber
PyPDF2 dependency as a fallback. Scanned PDFs are detected as a limitation because these libraries are not
OCR engines. [10]
Level 1 showed an “LLM Generator” block without a concrete model. Stage 2 selects
Unspecified local generator FLAN-T5-small as an optional local generator because its model file is much smaller
than many current LLMs and it can be run without a commercial API. [11]
Stage 2 treats SDG 4 as the primary alignment and SDG 9 as secondary. Any SDG 16
SDG claims too broad connection is described only as an indirect academic-integrity benefit, not as a
measurable primary impact.
The number of papers is now a configurable operating target, not a guarantee. Actual
50-paper limit stated as a guarantee capacity depends on page count, extraction quality, available RAM, and
embedding/index size.
2. Implementation Quality
2.1 Core Functionality & Architecture
The revised architecture is intentionally modular. Each stage has one technical responsibility
and produces an output that can be inspected independently. This makes debugging easier and also
makes the viva easier because a failure can be traced to ingestion, chunking, retrieval, generation, or
verification instead of being hidden inside one large script.
3

---

## PDF page 4
Figure 1: Revised Stage 2 architecture with local semantic and offline validation profiles
2.1.1 PDF Ingestion and Validation
Only PDF files are accepted in the present scope. The ingestion layer checks that a path exists,
rejects non-PDF input, rejects empty files, and stops with a readable message when a password-
protected document is encountered. Text is first extracted with pypdf page by page. If a page
contains very little extractable text, pdfplumber is tried as a second parser. If the complete
document still contains no usable text, the application reports that the file is probably scanned and
requires OCR, which is deliberately outside the Stage 2 scope.
2.1.2 Chunking Policy
Chunking is sentence-aware and preserves the source filename and page number. The current
default is approximately 180 words per chunk with a 30-word overlap. The overlap reduces the
chance that a definition or argument is split exactly at a chunk boundary. This value is smaller than
the Level 1 proposal because the selected MiniLM model truncates long inputs; a smaller chunk
therefore preserves more of the text that is actually encoded. The exact value remains configurable
and can be tuned later using retrieval accuracy rather than intuition alone. The MiniLM model
documentation notes a limited input length, which is why shorter evidence chunks are preferred
here [8].
2.1.3 Embeddings, Indexing and Retrieval
The semantic profile uses sentence-transformers/all-MiniLM-L6-v2 to convert each evidence
chunk into a dense embedding. Chroma stores the chunk text, embedding and metadata on the local
machine. A user query is embedded using the same model, and the retriever returns the top-k
evidence chunks. The validation profile replaces dense embeddings with TF-IDF and Chroma with
a small in-memory index. This is useful for automated tests because it removes network and model-
download dependencies while preserving the same pipeline interfaces. MiniLM and Chroma are
used according to the published model and local-persistence documentation [7], [8].
4

---

## PDF page 5
2.1.4 Grounded Answer Generation
The generator receives only the retrieved evidence, not the entire PDF collection. In the
intended local configuration, FLAN-T5-small is prompted to answer only from that evidence and to
retain source markers such as [S1, p.5]. FLAN-T5-small was selected instead of a much larger
model because this is a microproject expected to run on a student laptop. The fallback generator is
extractive: it ranks evidence sentences and returns the most relevant ones with source markers. The
extractive path is less fluent, but it is highly useful for testing because the source relationship is
explicit and reproducible. FLAN-T5-small is used as the optional local generator based on its public
model card and license information [11].
2.1.5 Citation Verification Logic
Verification is performed after answer generation. The verifier first parses every [Sx, p.y]
marker and confirms that the marker points to a chunk that was actually retrieved. It then compares
the claim sentence against the cited chunk using a support score. In the offline profile the score
combines TF-IDF cosine similarity with lexical token overlap. The semantic profile can replace this
component with MiniLM similarity or, in later work, a natural-language-inference model. The
output uses three states: Verified, Needs Review and Unsupported. These labels are intentionally
more careful than saying that a mathematical score has proven or disproven a claim. This
verification step addresses the broader problem of fabricated or unsupported references reported in
prior studies of generative-AI academic/scientific writing [3].
support_score = 0.7 * semantic_or_tfidf_similarity + 0.3 * token_overlap
if support_score >= verified_threshold: label = "Verified"
elif support_score >= review_threshold: label = "Needs Review"
else: label = "Unsupported"
The default thresholds in the current test profile are configuration values, not universal
constants. For the final evaluation, the team should label a small set of supported, borderline and
unsupported claims manually and choose thresholds that give an acceptable precision/recall balance
on that labelled set. More advanced retrieve-generate-critique systems such as Self-RAG show a
stronger learned alternative, but at greater implementation complexity [4].
5

---

## PDF page 6
2.2 Source Code Structure
Figure 2: Stage 2 source-code layout and module decomposition
The code is divided by responsibility instead of placing the complete system in app.py. Data
classes in models.py keep page, chunk, retrieval and verification objects explicit. pipeline.py is the
only orchestration layer; it calls the ingestion, chunking, index, generator and verifier modules. This
separation reduces side effects and allows the automated tests to exercise each unit without starting
a graphical interface.
Naming follows standard Python conventions: modules and functions use lowercase
snake_case, classes use PascalCase, constants use uppercase, and functions that can fail raise
explicit exceptions instead of silently returning empty output. Short docstrings explain non-obvious
decisions, while comments are used for implementation reasoning rather than restating each line.
Table 2: Stage 2 source-code modules and primary responsibilities
Module Primary responsibility
src/pdf_ingestion.py File validation, pypdf extraction, pdfplumber fallback, scanned-PDF detection
src/chunking.py Sentence-aware chunking with overlap and page/source metadata
src/embeddings.py MiniLM semantic backend and TF-IDF validation fallback
src/vector_store.py Persistent Chroma adapter plus deterministic in-memory test store
src/generator.py Local FLAN-T5-small option and extractive grounded fallback
src/verifier.py Citation-marker parsing, support scoring and status assignment
src/pipeline.py End-to-end orchestration and public index/ask methods
tests/test_core.py Ten automated validation, retrieval and verification tests
app.py Streamlit user interface
6

---

## PDF page 7
2.3 Execution & Outputs
A reproducible validation run was executed using the Level 1 report as input. The run used
Python 3.13.5, pypdf, pdfplumber and scikit-learn in the offline validation profile. The same
interfaces are used by the semantic profile, so the test verifies the control flow even when optional
MiniLM, Chroma, Transformers and Streamlit packages are not loaded. The document contained 11
pages and was split into 28 chunks. For the query “What technology stack is listed in Table 1
resource selection and rationale?”, the first retrieved chunk came from page 5 and the generated
answer cited that page. The citation verifier produced two Verified results for the two returned
evidence statements.
Figure 3: Actual automated-test and local-demo output from the Stage 2 prototype
7

---

## PDF page 8
Figure 4: Interface preview populated with the same actual runtime output
Figure 4 is an interface preview rather than a fabricated production screenshot: the answer,
chunk count and verification scores are populated from the actual demo run shown in Figure 3. The
submitted Streamlit app uses the same index and ask methods, so the interface layer does not
duplicate retrieval or verification logic.
2.4 Error Handling & Robustness
Table 3: Error-handling cases and implemented responses
Edge case Implemented handling
Wrong file type Reject before extraction with a clear “PDF only” message.
Empty file Reject instead of creating an empty index.
Encrypted PDF Stop and explain that password-protected PDFs are not supported.
Scanned/image-only PDF If no extractable text remains after both parsers, report that OCR is required.
Blank query Reject before retrieval so a meaningless vector search is not performed.
Zero chunks Prevent vector-store construction and raise a clear error.
top_k larger than collection Bound top_k to the number of indexed chunks.
Keep the fallback profile available and show an installation message rather than failing
Missing optional semantic packages
silently.
Invalid citation marker Mark it Unsupported because it does not resolve to retrieved evidence.
Borderline similarity Return Needs Review rather than pretending the system is certain.
8

---

## PDF page 9
3. Tools & Technology Usage
3.1 Tech Stack Specifications
Table 4: Technology stack specifications and selection rationale
Technology Role Reason for selection Cost status
Strong NLP/ML ecosystem and suitable for a single-
Python 3.10+ Core language language student project. Validation run also works on Free
Python 3.13.5.
Maintained successor package name to PyPDF2; page-
pypdf [10] Primary PDF extraction Open source
wise text extraction and metadata access.
pdfplumber Extraction fallback Useful when page layout is difficult for the primary parser. Open source
384-dimensional sentence embeddings for semantic Apache 2.0
all-MiniLM-L6-v2 [8] Primary embeddings
search; compact model suitable for local use. model
Allows retrieval and verifier tests to run without
TF-IDF / scikit-learn Offline validation fallback Open source
downloading model weights.
Stores documents, metadata and embeddings locally; no
Chroma [7] Persistent vector store Open source
database server is required for the project profile.
Instruction-tuned local text-to-text model. The safetensors
Apache 2.0
FLAN-T5-small [11] Optional local generator weight file is about 308 MB, which is practical compared
model
with multi-billion-parameter models.
Fast Python-native UI for upload, query, evidence and
Streamlit [9] Target user interface Open source
verification display.
Commit history, branching, code review and evidence of Free for normal
Git / GitHub Version control
individual contributions. student use
Can be added later, but the present pipeline is small
LangChain [6] Not required enough to keep direct orchestration and avoid an Optional
unnecessary dependency.
This stack was selected specifically to remove hidden cost. The semantic models can be
downloaded once and executed locally, Chroma can persist on local disk, and Streamlit can run on
localhost. The only practical costs are the team’s existing laptop, storage, electricity and internet
used for initial package/model downloads. No paid OpenAI, Gemini, Anthropic, Scopus or other
commercial API is required by the baseline design. The framework, storage, model, UI, PDF-
parsing and generator claims in this section are supported by the corresponding official
documentation [6]-[11].
3.2 Development & Deployment Environments
Table 5: Development and deployment environment
Item Stage 2 specification
Operating system Windows 10/11 or Linux; no OS-specific feature is required.
3.10 or later; use one fixed version in the team repository once the final environment is
Python
created.
Virtual environment venv: python -m venv .venv, followed by dependency installation from requirements.txt.
IDE VS Code, PyCharm Community, or any Python-capable editor.
Local execution streamlit run app.py for UI; python run_demo.py for a reproducible command-line check.
.chroma/ directory for the semantic Chroma profile; excluded from Git if generated
Persistence
locally.
Hardware target 8 GB RAM laptop, CPU-only accepted; generation latency may be slower than retrieval.
Localhost is sufficient for evaluation. A cloud deployment is not required for Stage 2 and
Deployment
is deliberately not promised.
9

---

## PDF page 10
3.3 Version Control & CI/CD
The repository should use a simple main/feature workflow. main should contain only code that
passes the current test suite. Each member works in a short-lived branch such as feature/ingestion,
feature/verifier or feature/ui, then opens a pull request or performs an equivalent peer review before
merging. This is adequate for a three-member academic team and avoids the overhead of a complex
branching model.
Table 6: Integration prototype commit log
Integration prototype
Purpose
commit
df05016 feat: add PDF ingestion and chunking foundation
a6bb764 feat: add retrieval generation and citation verification pipeline
5acd899 test: add UI scaffold demo and automated validation
8b85be0 refactor: select smaller local FLAN-T5 model for 8GB laptops
latest fix: reduce chunk size to avoid MiniLM input truncation
The commit identifiers above belong to the local integration prototype prepared for this Stage 2
package. They must not be presented as evidence of an individual student’s work. Before
submission, each team member should commit their own modules from their own Git account so
that the “Individual Technical Role & Contribution” section is backed by genuine repository
history. Fabricated commit IDs would weaken the credibility of the report.
A lightweight CI job can run “python -m unittest discover -s tests -v” on every push. For this
microproject, automated unit tests are more valuable than adding Docker or a complicated
deployment pipeline only to satisfy terminology in the format.
4. SDG Consideration
4.1 UN Sustainable Development Goals (SDG) Alignment
The strongest alignment is SDG 4: Quality Education. The project attempts to make AI-assisted
academic reading more transparent by showing where an answer came from and by signalling when
a cited statement has weak support. This supports responsible use of AI in learning rather than
treating generated text as an unquestionable source. This emphasis on transparent and responsible
use of generative AI in education is consistent with UNESCO guidance [5].
SDG 9: Industry, Innovation and Infrastructure is a secondary alignment because the project
demonstrates a small reusable information-retrieval and verification pipeline built from open-source
components. The Stage 1 document also connected the work to SDG 16. Stage 2 treats that only as
an indirect academic-integrity connection: reducing fabricated or unsupported references can
support trust, but the microproject should not claim that it meaningfully measures institutional
justice or governance outcomes.
10

---

## PDF page 11
4.2 Impact & Sustainability Mapping
Table 7: Impact and sustainability mapping
Metric Stage 2 target / result How it is measured SDG relevance
Directly supports
INR 0 in the baseline local Use only local/open-source components
Paid API expenditure affordability under SDG
design for the core demo.
4.
Target: every factual answer
Traceability of Count answer sentences with valid [Sx, Makes source checking
sentence carries a source
generated claims p.y] markers. systematic.
marker
Measured as verifier flags on Compare flags with a manually checked Reduces blind trust in
Unsupported citations
labelled test claims set; report precision/recall later. generated references.
Same PDF + same query
Run the deterministic fallback as a Improves reliability for
Reproducibility should produce the same
regression test. classroom evaluation.
extractive validation output
CPU-only operation on an Avoids requiring
Record indexing and response time during
Hardware accessibility ordinary 8 GB laptop is the specialist GPU
final demo.
design target infrastructure.
Configurable, not guaranteed Report pages/chunks and stop if Prevents exaggerated
Paper capacity
at 50 papers memory/latency becomes unacceptable. scalability claims.
5. Individual Technical Role & Contribution
5.1 Individual Work Breakdown
The responsibility mapping below is carried forward from the Level 1 RACI allocation and
converted into concrete Stage 2 technical ownership. It is intended to guide genuine implementation
work and to make individual viva preparation clear. The final submitted copy should be cross-
checked against the team’s actual Git history before signatures are taken.
Table 8: Individual Stage 2 work breakdown
Team member Primary Stage 2 ownership Expected technical artifacts
src/verifier.py, verification thresholds/configuration,
Citation verification module; system-
Rishabh Jain invalid-marker handling, review of architecture and status
design review; verifier test cases
labels
src/pipeline.py, app.py, integration between
Pipeline integration and UI; retrieval
Purv Jain retrieval/generator/verifier, end-to-end demo and
flow
integration branch
PDF ingestion/testing/documentation src/pdf_ingestion.py, test-case preparation, edge-case
Bhavya Soni
support documentation, literature/SDG mapping, report integration
All members should still understand the complete pipeline. Ownership is used to establish
accountability, not to create isolated knowledge. During evaluation, any member should be able to
explain why the chunk size was changed, how retrieval scores differ from citation-support scores,
and why low similarity is not automatically equivalent to hallucination.
5.2 Technical Artifacts
 Module-level source files with clear ownership rather than one shared app.py edited by
everyone.
 At least one meaningful commit per implemented feature from the actual student account that
performed the work.
11

---

## PDF page 12
 Automated tests written alongside the module, especially for edge cases and citation
verification.
 A short pull-request or peer-review note when integrating a feature into main.
 No invented contribution percentages, PR numbers or commit hashes. Repository evidence
should match what was actually done.
6. Team Collaboration & Workflow
6.1 Task Distribution & Timeline
Figure 5: Relative six-week implementation plan based on the Level 1 project timeline
The order is intentionally dependency-driven. Ingestion and chunking must stabilize before
retrieval can be evaluated; retrieval must return page-aware evidence before the verifier can be
meaningful; and the user interface comes after the pipeline API is stable. This prevents the team
from spending time polishing a front end while the evidence chain underneath it is still changing.
Table 9: Task distribution and exit conditions
Work item Owner / lead Exit condition
Same requirements file and sample set available to all
Environment and sample PDFs All members
members.
Page metadata preserved; scanned/invalid files handled;
Ingestion and chunking Bhavya lead, Purv review
chunk size verified.
Correct evidence page appears within top-k for prepared
Retrieval/indexing Purv lead, Rishabh review
questions.
Valid markers resolve; unsupported markers are
Citation verifier Rishabh lead, Bhavya review
flagged; thresholds documented.
Upload, index, query, answer, verification and evidence
UI integration Purv lead
views operate through one interface.
Automated suite passes and every report claim is
Testing and report Bhavya lead, all review
checked against actual code/output.
12

---

## PDF page 13
6.2 Communication & Integration
The Level 1 plan states that the team uses periodic check-ins. For Stage 2, each check-in should
end with three recorded items: what changed since the previous review, what is blocked, and what
will be merged next. A short record is more useful than lengthy meeting minutes because it creates
a trace between the timeline and the repository.
Integration should happen feature by feature. The feature owner first runs unit tests locally,
another member reads the change, and only then is it merged. If two branches touch the same file,
the conflict is resolved by comparing the intended behavior and rerunning the tests after the merge,
not by choosing “ours” or “theirs” blindly. The same rule applies to report edits: technical
statements must match the current code, even if an older statement appeared in Level 1.
7. Testing, Viva & Understanding
7.1 Test Cases & Results
The current automated test suite contains ten tests. They were executed against the Stage 2
validation profile and the actual Level 1 PDF where applicable. All ten tests passed. These tests do
not claim that the final semantic verifier is already scientifically calibrated; they prove that the
implemented control flow and error-handling rules behave as specified.
Table 10: Automated test cases and results
ID Input / action Expected output Actual output Status
TC-01 Upload a .txt file Reject non-PDF input PDFIngestionError raised Pass
Return all pages and project-title
TC-02 Extract Level 1 report PDF 11 pages extracted; title text present Pass
text
Long synthetic page, 120-word test Create multiple chunks and keep Multiple chunks created; metadata
TC-03 Pass
chunks page metadata preserved
TC-04 Overlap equal to target size Reject invalid chunk configuration ValueError raised Pass
Query: component that stores vector
TC-05 Rank ChromaDB chunk first Relevant chunk C1 ranked first Pass
embeddings
TC-06 top_k=10 with only 3 chunks Return at most 3 results 3 results returned Pass
TC-07 Citation [S9, p.2] when only S1 exists Mark citation Unsupported Unsupported Pass
Supported paraphrase with valid
TC-08 Mark as Verified Verified Pass
marker
TC-09 Blank query after indexing Reject query before retrieval ValueError raised Pass
Retrieve page 5 and return source- Top result p.5; verification results
TC-10 Resource-plan question on real PDF Pass
marked answer returned
The full run completed with “Ran 10 tests ... OK”. In the demonstration query, the top retrieval
score belonged to page 5 of the Level 1 report, and both output statements carrying [S1, p.5] were
labelled Verified in the offline support-scoring profile.
13

---

## PDF page 14
7.2 Technical Viva Preparation
Table 11: Technical viva questions and expected answers
Likely viva question Expected technical answer
Why RAG instead of asking an LLM RAG supplies external evidence at query time. The answer can be traced to retrieved
directly? passages, which is essential for this project’s citation-verification objective.
The Level 1 report mixed tokens and words and proposed chunks that can exceed
Why was chunk size changed from Stage
MiniLM’s effective input length. Smaller chunks reduce silent truncation and improve
1?
page-level evidence precision.
No. It measures relatedness in an embedding space. A high score is supportive
Is cosine similarity proof that a citation is
evidence, not logical entailment. That is why the system has a Needs Review state and
correct?
configurable thresholds.
A low score can be caused by paraphrasing, poor extraction or wrong chunking.
Why not call every low score a
“Unsupported” is a safer system label; hallucination is an interpretation requiring
hallucination?
evaluation.
It can persist embeddings and metadata locally and does not require a separately
Why Chroma?
managed database server for this scale.
It allows deterministic unit/integration testing when neural model weights are not
Why keep a TF-IDF fallback?
downloaded, and it keeps the project demonstrable without paid or hosted services.
It is a compact instruction-tuned local model with a much smaller weight file than
Why FLAN-T5-small? many modern LLMs. The trade-off is weaker generation quality but greater feasibility
on ordinary laptops.
Retrieval score ranks chunks against the user question. Verification score compares an
What is the difference between retrieval
answer claim with the cited evidence. They solve different problems and should not be
score and verification score?
treated as interchangeable.
pypdf and pdfplumber cannot reliably read text that exists only as an image. The
What happens with a scanned PDF?
system reports the limitation; OCR is a possible future extension.
What would be the next technical Build a manually labelled claim-evidence set, calibrate thresholds, and compare the
improvement? current similarity verifier with a small NLI/cross-encoder verifier.
7.3 Design Trade-offs
Table 12: Major design trade-offs
Decision Trade-off
Local execution removes recurring cost and privacy concerns but is slower and less
Local model vs hosted API
capable on CPU.
MiniLM is compact and fast; larger models may improve retrieval but increase
MiniLM vs larger embeddings
download, RAM and inference time.
Chroma provides persistence and metadata search; in-memory TF-IDF is simpler and
Chroma vs plain in-memory store
more deterministic for automated tests.
Extractive output is less natural but easier to verify; abstractive FLAN-T5 output is
Extractive vs abstractive generation
more readable but can introduce unsupported wording.
Similarity is lightweight and easy to explain; NLI can better model entailment but adds
Similarity verifier vs NLI verifier
model size and evaluation complexity.
References
[1] P. Lewis et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” Advances in Neural
Information Processing Systems, 2020.
[2] Y. Gao et al., “Retrieval-Augmented Generation for Large Language Models: A Survey,” arXiv:2312.10997,
2023.
[3] S. R. Athaluri et al., “Exploring the Boundaries of Reality: Investigating Artificial Intelligence Hallucination
in Scientific Writing Through ChatGPT References,” Cureus, vol. 15, no. 4, 2023.
[4] A. Asai et al., “Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection,” ICLR, 2024.
[5] UNESCO, “Guidance for Generative AI in Education and Research,” UNESCO Publishing, 2023.
[6] LangChain, “Learn - LangChain Documentation,” documentation describing RAG and application-building
components, accessed Oct. 2026.
14

---

## PDF page 15
[7] Chroma, “Chroma Documentation,” open-source retrieval and local persistence documentation, accessed Oct.
2026.
[8] Sentence Transformers, “Semantic Textual Similarity” documentation and “all-MiniLM-L6-v2” model card,
accessed Oct. 2026.
[9] Streamlit, “Streamlit Documentation,” open-source Python data/AI application framework documentation,
accessed Oct. 2026.
[10] pypdf, “CHANGELOG” and “Extract Text from a PDF,” documentation noting the PyPDF2-to-pypdf
package move and OCR limitations, accessed Oct. 2026.
[11] Google / Hugging Face, “google/flan-t5-small” model card and files, Apache-2.0 licensed model, accessed
Oct. 2026.
15
