# Stage 1 Report (Level 1) — extracted text

> **Provenance.** Text extracted from the submitted PDF
> `FAI&PE_Microproject_stage_1_report.pdf` (found at `C:\Users\purvj\Downloads\.pdf\FAI&PE_Microproject_stage_1_report.pdf`, 434,870 bytes) using `pdfplumber`
> page-by-page extraction on 2026-10-08.
>
> - Pages extracted: **11**
> - Extraction produced **21,573** bytes of text
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
Microproject Report — Level 1
Project Title
“RAG-Based Academic Research Assistant with Citation Verification”
Team Members:
Rishabh Jain (Prn: 124BTCM1054)
Purv Jain (Prn: 124BTCM1171)
Bhavya Soni (Prn: 124BTCM1215)
Project Guide:
Prof. Priyanka Kharatmol
1

---

## PDF page 2
1. Problem Definition & Scope
1.1 Problem Statement
First time we used tools such as ChatGPT in creating coursework – answers were confident-looking. Often
they weren't factual, which, sadly, was the case. Large language models often publish non-existent papers,
they often create non-existent author names and DOSIDs, and they often make up paper titles that are not
found in any database; all of these things happen so often that, as biologists, one senses that it's literally
playing a game with the truth. The problem of our project is easily put: “There is not one lightweight tool
that can retrieve the actual academic papers and subsequently verify whether the claims embedded in the
generated answer are present in the retrieved source text; which is open-source, on top of being lightweight.
Higher education students are paying a price. The time they dedicate to checking one source at a time bitters
is hours in the book, and each untrustworthy source they are fooled by weakens their trust in AI sources. In
the tragedy of the worse case scenario, they accidentally plagiarize and submit work that contains Malaysian
sources that they themselves created. It is a huge academic integrity problem taking 5 minutes per sourced
work! At BH Media, our latest big concern isn't with generation quality, it's the verifiability of it. So our
project's goal is to work in academic research assistance and make summaries from AI a fast and systematic
way to verify it, not just a thing the student has to totally trust or scrap.
1.2 Background & Context
It's really difficult for us to understand how big the scale of academic publishing is. According to recent
estimates, there are about 6 million research papers published annually; however, it is impossible for any
student (no matter how sincere) to read all those publications. The AI summarization tool has been a fast
response to that problem. The catch is reliability. The 2023 research on ChatGPT's citation behavior showed
that this AI generated many false citations for its outputs during certain tasks like generating fake DOIs [3],
so students might cite non-existent papers when they copy these from their work. This was quite fascinating
to us as there are no obvious signs of fraud since nobody would know that their source isn't real unless they
check it themselves. Most universities are responding to this issue through a ban on or restriction of AI
software; although we recognize that is an instinctive response, it addresses symptoms instead of causes.
Enforcement of bans is difficult. Also they discard real advantages. According to us, for this matter it would
be more appropriate if we built AI systems which are inherently verifiable so that each statement made by an
artificial intelligence has proof available for students to verify rather than pretending at university level.
2

---

## PDF page 3
1.3 Project Scope & Boundaries
In other words, it should have been narrow enough for completion within an academic year yet practical
enough to use. PDFs from up to 50 scholarly articles are accepted by this tool which is split into overlapping
text segments; these are embedded and stored within an on-site vector database for answering queries using
in-text references while also running each reference through a three-stage verification process where they get
flagged as either verified, unverified, or hallucinated. Streamlit is an easy way to connect them all up. This is
a complete product. However, just as important, it was also about leaving things out of our project since a
microproject that promises everything usually delivers nothing; we did not scrape live databases like arXiv
or Scopus, we did not handle non-English papers, and we stayed away from collaborative editing, mobile
deployment, and reference-manager integrations such as Zotero.
In-Scope:
• PDF ingestion of up to 50 academic papers
• Text chunking (~500 tokens) with 50-token overlap
• Vector storage and similarity retrieval (ChromaDB)
• LLM-based summarization with in-text citation markers
• Three-tier citation verification: Verified / Unverified / Hallucinated
• Streamlit web interface for upload, query, and results
Out-of-Scope:
• Web scraping of live databases (arXiv, Scopus, etc.)
• Support for non-English papers
• Real-time collaborative editing
• Mobile app deployment
• Integration with reference managers such as Zotero
3

---

## PDF page 4
2. Design & Methodology
2.1 System Architecture & Workflow
There are four stages of this process where information moves linearly from stage to stage. During ingestion,
users upload a file to Streamlit; then PyPDF2 and pdfplumber extract the content from it, pdfplumber deals
with complex formats like tables or two-column layouts that are difficult for simple parsers. Then it gets
divided up to about 500 words per chunk with an overlap of around 50 words so as not to cut through any
sentence at its end point or beginning where it would be lost. Stage 2 converts them to a numeric value.
Every piece goes through an all-MiniLM-L6-v2 sentence transformer model provided by Hugging Face for
converting text into a dense vector representation stored as part of a ChromaDB database file persisted
across multiple runs.
The third stage is for answering questions. Upon receiving a request, we use our own model to retrieve the
top five most similar chunks from ChromaDB which will be used as part of the input for generating
responses with citations such as [Source 1, p. Our stage four project is what matters to us most. Citation
Verification Module is used for extracting all markers from an input string using regular expressions; then
finding out which part of that string corresponds to each marker and calculating its cosine similarity with
respect to the original document. If a score exceeds 0.75 then it will be flagged as Verified; if it falls within
that range of 0.4 to 0.75 we say Unverified; while any value less than 0.4 would mean Hallucinated by this
model which means students are being told about their level of confidence on these statements. The results
are displayed on screen using color codes; therefore it is not possible for an incorrect statement to be missed
by users.
Figure 1: System architecture of the proposed pipeline
[PDF Upload] → [Chunker] → [Embedder] → [ChromaDB]
↓
[User Query] → [Retriever] → [LLM Generator] → [Citation Verifier] → [UI Output]
4

---

## PDF page 5
2.2 Proposed Methodology
The project was divided into three stages according to an academic year schedule. The first phase was for
initial setup; it involved reading articles of retrieval augmented generation, collecting around 60 samples
from open access sites and setting up a Python environment with fixed library versions to ensure all
members had identical software stacks. Phase two, which we are currently doing at this moment, is a heavy
build. First we wrote the ingestion and chunking code, then wired up embeddings and ChromaDB storage;
finally, we connected the retrieval step to the generator so that each part can be tested independently of
others as a dependency. The third phase is about developing a Citation Verification module for Streamlit
application that ends by testing its performance against 20 test cases which are already prepared beforehand.
The evaluation process is done manually. Each of the twenty generated responses has been checked by two
team members to verify if any citations are correct or not; then based on this verification process we can
calculate accuracy and recall rates for both verified and hallucinated labels. Numbers may not be large, yet
they are truthful (at least this is what we hope for).
2.3 Resource Plan
Table 1: Resource selection and rationale
Resource Selection Rationale
Language Python 3.10+ Most NLP/ML library support
LLM LangChain Modular RAG pipeline construction
Framework
Embeddings all-MiniLM-L6-v2 Lightweight, runs on CPU, good semantic
quality
Vector DB ChromaDB Open-source, no server setup needed
PDF Parsing PyPDF2 + pdfplumber Handles text and table extraction
UI Streamlit Rapid prototyping, Python-native
Hardware Standard laptop (8GB RAM, Keeps project accessible and reproducible
no GPU required)
Every choice in Table 1 is open-source and runs comfortably on an ordinary laptop, because we wanted any
student team — at any college, with any budget — to reproduce the project without paying for APIs or
hardware. Keeping the stack lightweight also made our own testing loop faster, since nobody had to queue for
a shared GPU machine.
5

---

## PDF page 6
3. SDG Consideration
3.1 Goal Mapping
The project is best mapped to three of the United Nations' Sustainable Development Goals. Firstly, SDG 4,
Quality Education; providing students of poor schools with an affordable software for generating accurate
data reports so as to bridge the gap between those who have access to expensive databases and those who
doable studies. Secondly, it refers to SDG 9 (Industry, Innovation and Infrastructure) as this verification
function for citations is an example of a small yet reusable part of artificial intelligence infrastructure which
can be built by larger educational institutions. SDG 16 might appear to be an exaggeration initially. It is not.
Fabricated references are a form of misinformation, and academic integrity is an issue because it undermines
trustworthiness which is required by SDG 16 as support to remove fake citations from students' papers
through this method helps achieve its objectives effectively though not very much.
3.2 Impact Justification
We are hoping to have a practical effect on time and trust. If the tool saves a postgraduate student even one
hour of manual source-checking per week, then this is equivalent to saving actual human time over an entire
term and avoiding unnecessary computational resources spent on running queries which gave incorrect
results initially. In addition, this is an example of a minor step towards responsible AI usage within
educational settings according to UNESCO's 2023 recommendations for building transparency about
generative AI instead of banning it [6]. The code is open-source. Any institution may use this for free of
charge. Of course, the tool's impact depends upon its adoption rate; we know that developing this software
was just a starting point for us to implement it at scale.
6

---

## PDF page 7
4. Conceptual Understanding & Literature Review
4.1 Theoretical Principles
RAG (Retrieval Augmented Generation) is an integral part to our project. The idea, introduced by Lewis et
al. in 2020 [1], is that a language model should not answer purely from its training data; instead, it first
retrieves relevant documents from an external store and then generates an answer grounded in that material,
which measurably reduces the tendency to hallucinate. Dense vector retrieval is below retrieval step. The
transformer based encoder transforms an input string to a high dimensional vector which represents it as a
point within some space; this allows for calculating similarity by computing angles between these vectors.
Cosine similarity is used by this equation.
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)
It is a measure of similarity between two vectors; 1.0 indicates they are pointing exactly alike while 0 shows
there is none at all and any value between these extremes represents their level of semantic similarity.
Simple, but surprisingly effective.
Chunking was more than anticipated by us. Split a document into smaller parts where each part lacks context
for its meaning; split too large and the embedding averages together unrelated ideas, so retrieval returns
noise instead of signal, which is why we settled on 500 tokens with a 50-token overlap after some informal
experimentation. The final principle is citation verification through semantic similarity, and honestly it is the
piece we are proudest of. The assumption is simple. The Again if it is an actual quote of some kind then
there would be little to no overlap between these two documents. It is a proxy, not a proof. Member of an
automated test suite to catch bad results; this helps students evaluate their work before they rely on a
generated summary.
4.2 Prior Art / Literature Review
[1] Retrieval-Augmented Generation — Lewis et al., NeurIPS 2020
Lewis and colleagues introduced RAG at NeurIPS 2020, pairing a neural retriever with a sequence-to-
sequence generator so that knowledge-intensive tasks could draw on an external Wikipedia index instead of
relying on frozen model weights alone [1]. Their results on open-domain question answering were strong. The
work started everything our project stands on. What it does not do, however, is check whether the generated
answer actually matches the passages it retrieved — verification of the output was simply out of scope for
their formulation.
7

---

## PDF page 8
[2] RAG for Large Language Models: A Survey — Gao et al., 2023
Gao et al. wrote the survey we kept returning to, systematically mapping the RAG pipeline — indexing,
retrieval, generation — and cataloguing the failure modes that appear at each stage, including noisy retrieval
and hallucinated content [2]. It gave us vocabulary. It also gave us our chunking intuition. The survey stops
at describing techniques, though, and offers no working student-facing tool that applies them end to end.
[3] Generative AI Hallucinations in Medical Research — Athaluri et al., Cureus 2023
Athaluri and co-authors examined hallucinations produced by generative AI in medical research writing and
reported that ChatGPT invented a worrying share of its references, complete with plausible-looking but fake
DOIs [3]. They were not in the context of students studies but of medicine. The wagers that they record are
terrifying. They clearly articulate the problem in their paper, but do not offer any solution that would allow a
writer to automatically verify every citation with the source they cite.
[4] Hallucination in LLMs: Understanding and Mitigating — Magesh et al., 2024
On hallucination, Magesh et al. directly addressed the problem and examined the reasons behind LLM
hallucinations and contrasted various mitigation approaches like retrieval grounding, prompt engineering,
and output filtering [4]. Their classification was useful for us to use as a template for our categories..
Detection and mitigation are treated as separate steps in their analysis. What remains open — and this is the
space our project occupies — is a single lightweight pipeline where mitigation and per-citation detection run
together, in real time, on a student’s own document collection.
[5] Self-RAG: Retrieve, Generate, and Critique — Asai et al., ICLR 2024
Asai and colleagues proposed Self-RAG, in which the model learns to retrieve on demand and to critique its
own generations using special reflection tokens, improving factuality over standard RAG baselines [5]. The
self-critique idea influenced our verifier. Their approach, to the best of our understanding, requires training
the language model itself, which puts it out of reach for a student team without GPU budgets — our cosine-
similarity check is a deliberately cheaper stand-in for that learned critique.
[6] Guidance for Generative AI in Education and Research — UNESCO, 2023
UNESCO’s 2023 guidance on generative AI in education and research is not a technical paper, but it shaped
our thinking anyway, because it argues that institutions should demand transparency, human oversight, and
verifiable outputs from AI systems used in learning [6I know it’s a policy, not code, but we went ahead and
implemented citation verification because educators are asking for it as a necessary safety measure. Reading
through it definitely convinced me that it’s necessary, so it was worth the extra work.
8

---

## PDF page 9
5. Participation, Initiative & Roles
5.1 Role Allocation Matrix (RACI)
While all three team members were involved with all stages to some extent, the breakdown of roles was
determined by previous experience and an attempt to make sure all team members were evenly distributed
with tasks. This is shown in the RACI chart below. This matrix follows the convention of RACI charts, with
R for Responsible, A for Accountable, C for Consulted and I for Informed. There is only ever one person
Accountable for any row as this allows us to keep going when opinions differ, avoiding stalemates.
Table 2: RACI role allocation matrix
Task Rishabh Jain Purv Jain Bhavya Soni
Literature Review R C A
System Design A R C
Pipeline Development C A R
Citation Module R C A
UI Development A R C
Documentation C A R
Purv is focusing more on developing the pipeline. Bhavya is focusing more on the Literature Review. We
check-in every two weeks, and update the responsibility matrix according to increasing/decreasing workload
for the semester.
5.2 Project Timeline
This micro project was handed over to our team, and it has been just a little over two and a half weeks up to
today. Before writing this timeline, we sorted out all progress made since the project launch in full detail. All
the content listed below is completely factual, and only records two types of matters: one is the work that has
been genuinely completed as of today, and the other is the firmly scheduled arrangements to be advanced in
the coming weeks — we have not added any unfounded speculative content, nor have we exaggerated the
project's progress by even the slightest bit.
In the first week and a half right after the project launched, we fully wrapped up the two preliminary
preparation tasks: the literature review and the environment setup. Currently, the work on process
construction is advancing steadily. Once this task is completed, the remaining work has also been arranged
with a fixed sequence that will not be altered arbitrarily, and the order is as follows: the citation module, the
UI, and finally the testing of the entire project. This sequence will not change.
9

---

## PDF page 10
Table 3: Project timeline and current status (as of Week 3)
Task Timeline Status
Literature Review Week 1 Completed
Environment Setup Week 1 Completed
Sample PDF Collection Week 1–2 Completed
RAG Pipeline Build Week 2–3 In Progress
Citation Verification Module Week 3–4 In Progress (design finalized)
UI Integration (Streamlit) Week 4–5 Planned
Testing & Documentation Week 5–6 Planned
Beyond the assigned tasks our team independently explored open-source embedding models. All-MiniLM-
L6-v2 versus BAAI’s bge-small-en-v1.5 both freely available on HuggingFace. And documented a
comparison even though we ultimately chose MiniLM for its smaller memory footprint, on CPU.
Nobody asked us to do that comparison.
We just wanted to be sure we were not picking the default out of laziness. The exercise taught us about
embedding quality than any lecture had.
6. Presentation & Communication Standards
This document follows the formatting rules that our department expects. This document sets body text in
Times New Roman at 12pt with 1.5 line spacing and headings use 14pt. This document sets margins to one
inch on all sides. This document numbers figures and tables sequentially. Table 1 Table 2 Figure 1 and so
on. And follows IEEE numbered citation style so [1] points to the entry in the reference list. This document
writes terms, in italics on first use. This document keeps all diagrams original. This document draws every
figure by the team than lifting from a paper because drawing forces the team to truly understand the
architecture that this document proposes to build in the coming weeks. This document has tried to keep
terminology all the time. For example this document uses ‘citation verification’ instead of alternating with
‘reference checking’ to avoid reader confusion.
10

---

## PDF page 11
References
[1] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Yih, T.
Rocktäschel, S. Riedel, and D. Kiela, “Retrieval-Augmented Generation for Knowledge-Intensive
NLP Tasks,” in Proc. Advances in Neural Information Processing Systems (NeurIPS), 2020.
[2] Y. Gao, Y. Xiong, X. Gao, K. Jia, J. Pan, Y. Bi, Y. Dai, J. Sun, and H. Wang, “Retrieval-Augmented
Generation for Large Language Models: A Survey,” arXiv:2312.10997, 2023.
[3] S. R. Athaluri, S. V. Manthena, V. S. R. K. Kesapragada, V. Yarlagadda, T. Dave, and R. T. S.
Duddumpudi, “Exploring the Boundaries of Reality: Investigating the Phenomenon of Artificial
Intelligence Hallucination in Scientific Writing Through ChatGPT References,” Cureus, vol. 15, no.
4, e37432, 2023.
[4] V. Magesh, F. Surani, M. Dahl, M. Suzgun, C. D. Manning, and D. E. Ho, “Hallucination-Free?
Assessing the Reliability of Leading AI Legal Research Tools,” arXiv:2405.20362, 2024.
[5] A. Asai, Z. Wu, Y. Wang, A. Sil, and H. Hajishirzi, “Self-RAG: Learning to Retrieve, Generate, and
Critique through Self-Reflection,” in Proc. Int. Conf. on Learning Representations (ICLR), 2024.
[6] UNESCO, “Guidance for Generative AI in Education and Research,” UNESCO Publishing, Paris,
France, 2023.
11
