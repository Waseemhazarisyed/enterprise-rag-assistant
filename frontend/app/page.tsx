"use client";



import { useEffect, useState } from "react";

import type { User } from "@supabase/supabase-js";



import { supabase } from "../lib/supabase";
import { apiFetch } from "../lib/api";



type DocumentItem = {

  id: number;

  filename: string;

  file_type: string;

  status: string;

  created_at: string;

};



type Metrics = {

  total_requests: number;

  successful_requests: number;

  failed_requests: number;

  average_embedding_latency_ms: number;

  average_retrieval_latency_ms: number;

  average_llm_latency_ms: number;

  average_total_latency_ms: number;

  average_top_similarity: number;

};



type ChatSource = {

  filename: string;

  page_number: number;

  chunk_index: number;

  similarity: number;

};



type ChatMessage = {

  role: "user" | "assistant";

  content: string;

  sources?: ChatSource[];

};



type RetrievalItem = {

  chunk_id: number;

  document_id: number;

  page_number: number;

  chunk_index: number;

  similarity: number;

};



export default function Home() {

  // -----------------------------------

  // AUTH

  // -----------------------------------

  const [user, setUser] = useState<User | null>(null);

  const [authLoading, setAuthLoading] = useState(true);



  const [authMode, setAuthMode] =

    useState<"signin" | "signup">("signin");



  const [email, setEmail] = useState("");

  const [password, setPassword] = useState("");



  const [authSubmitting, setAuthSubmitting] =

    useState(false);



  const [authError, setAuthError] = useState("");

  const [authMessage, setAuthMessage] = useState("");



  // -----------------------------------

  // DOCUMENTS

  // -----------------------------------

  const [documents, setDocuments] =

    useState<DocumentItem[]>([]);



  const [loadingDocuments, setLoadingDocuments] =

    useState(false);



  const [documentError, setDocumentError] =

    useState("");



  // -----------------------------------

  // SELECTED DOCUMENT

  // -----------------------------------

  const [

    selectedDocumentId,

    setSelectedDocumentId,

  ] = useState<number | null>(null);



  // -----------------------------------

  // UPLOAD

  // -----------------------------------

  const [uploading, setUploading] =

    useState(false);



  const [uploadError, setUploadError] =

    useState("");



  const [uploadSuccess, setUploadSuccess] =

    useState("");



  // -----------------------------------

  // DELETE

  // -----------------------------------

  const [

    deletingDocumentId,

    setDeletingDocumentId,

  ] = useState<number | null>(null);



  // -----------------------------------

  // METRICS

  // -----------------------------------

  const [metrics, setMetrics] =

    useState<Metrics | null>(null);



  const [loadingMetrics, setLoadingMetrics] =

    useState(false);



  const [metricsError, setMetricsError] =

    useState("");



  // -----------------------------------

  // CONVERSATION

  // -----------------------------------

  const [

    conversationId,

    setConversationId,

  ] = useState<number | null>(null);



  const [

    conversationError,

    setConversationError,

  ] = useState("");



  // -----------------------------------

  // CHAT

  // -----------------------------------

  const [question, setQuestion] =

    useState("");



  const [messages, setMessages] =

    useState<ChatMessage[]>([]);



  const [sending, setSending] =

    useState(false);



  // ===================================

  // AUTH SESSION

  // ===================================



  useEffect(() => {

    async function loadSession() {

      try {

        const {

          data: { session },

        } = await supabase.auth.getSession();



        setUser(session?.user ?? null);

      } catch (error) {

        console.error(

          "Failed to load auth session:",

          error

        );

      } finally {

        setAuthLoading(false);

      }

    }



    loadSession();



    const {

      data: { subscription },

    } = supabase.auth.onAuthStateChange(

      (_event, session) => {

        setUser(session?.user ?? null);

        setAuthLoading(false);

      }

    );



    return () => {

      subscription.unsubscribe();

    };

  }, []);



  // ===================================

  // LOAD APP DATA AFTER LOGIN

  // ===================================



  useEffect(() => {

    if (!user) {

      setDocuments([]);

      setMetrics(null);

      setMessages([]);

      setConversationId(null);

      setSelectedDocumentId(null);



      return;

    }



    loadDocuments();

    loadMetrics();

    startConversation();

  }, [user]);



  // ===================================

  // AUTH FUNCTIONS

  // ===================================



  async function handleAuth() {

    if (!email.trim() || !password.trim()) {

      setAuthError(

        "Please enter your email and password."

      );

      return;

    }



    try {

      setAuthSubmitting(true);

      setAuthError("");

      setAuthMessage("");



      if (authMode === "signup") {

        const {

          data,

          error,

        } = await supabase.auth.signUp({

          email: email.trim(),

          password,

        });



        if (error) {

          throw error;

        }



        if (!data.session) {

          setAuthMessage(

            "Account created. Check your email to confirm your account, then sign in."

          );



          setAuthMode("signin");

        } else {

          setAuthMessage(

            "Account created successfully."

          );

        }

      } else {

        const { error } =

          await supabase.auth.signInWithPassword({

            email: email.trim(),

            password,

          });



        if (error) {

          throw error;

        }

      }

    } catch (error) {

      console.error("Authentication error:", error);



      setAuthError(

        error instanceof Error

          ? error.message

          : "Authentication failed."

      );

    } finally {

      setAuthSubmitting(false);

    }

  }



  async function handleLogout() {

    try {

      await supabase.auth.signOut();



      setDocuments([]);

      setMetrics(null);

      setMessages([]);

      setConversationId(null);

      setSelectedDocumentId(null);

      setQuestion("");

    } catch (error) {

      console.error("Logout failed:", error);

    }

  }



  // ===================================

  // DOCUMENTS

  // ===================================



  async function loadDocuments() {

    try {

      setLoadingDocuments(true);

      setDocumentError("");



      const response = await apiFetch(

        "/documents"

      );



      if (!response.ok) {

        throw new Error(

          "Failed to load documents"

        );

      }



      const data = await response.json();



      setDocuments(data);

    } catch (error) {

      console.error(

        "Failed to load documents:",

        error

      );



      setDocumentError(

        "Could not connect to the backend."

      );

    } finally {

      setLoadingDocuments(false);

    }

  }



  // ===================================

  // METRICS

  // ===================================



  async function loadMetrics() {

    try {

      setLoadingMetrics(true);

      setMetricsError("");



      const response = await apiFetch(

        "/metrics/summary"

      );



      if (!response.ok) {

        throw new Error(

          "Failed to load metrics"

        );

      }



      const data = await response.json();



      setMetrics(data);

    } catch (error) {

      console.error(

        "Failed to load metrics:",

        error

      );



      setMetricsError(

        "Could not load metrics."

      );

    } finally {

      setLoadingMetrics(false);

    }

  }



  // ===================================

  // CONVERSATIONS

  // ===================================



  async function startConversation(): Promise<

    number | null

  > {

    try {

      setConversationError("");



      const response = await apiFetch(

        "/conversations",

        {

          method: "POST",

        }

      );



      if (!response.ok) {

        throw new Error(

          "Failed to create conversation"

        );

      }



      const data = await response.json();



      setConversationId(data.id);



      return data.id;

    } catch (error) {

      console.error(

        "Failed to create conversation:",

        error

      );



      setConversationError(

        "Could not start a conversation with the backend."

      );



      return null;

    }

  }



  // ===================================

  // UPLOAD

  // ===================================



  async function uploadDocument(file: File) {

    if (file.type !== "application/pdf") {

      setUploadError(

        "Please select a PDF file."

      );



      setUploadSuccess("");



      return;

    }



    try {

      setUploading(true);

      setUploadError("");

      setUploadSuccess("");



      const formData = new FormData();



      formData.append("file", file);



      const response = await apiFetch(

        "/documents",

        {

          method: "POST",

          body: formData,

        }

      );



      if (!response.ok) {

        const errorData =

          await response.json();



        throw new Error(

          errorData.detail ||

            "Failed to upload document."

        );

      }



      const data = await response.json();



      setUploadSuccess(

        `${data.filename} uploaded successfully. ${data.chunks_created} chunk(s) created.`

      );



      await loadDocuments();



      setSelectedDocumentId(data.id);



      setMessages([]);



      await startConversation();

    } catch (error) {

      console.error(

        "Upload failed:",

        error

      );



      setUploadError(

        error instanceof Error

          ? error.message

          : "Failed to upload document."

      );

    } finally {

      setUploading(false);

    }

  }



  // ===================================

  // DELETE

  // ===================================



  async function deleteDocument(

    documentId: number

  ) {

    const confirmed = window.confirm(

      "Are you sure you want to delete this document?"

    );



    if (!confirmed) {

      return;

    }



    try {

      setDeletingDocumentId(documentId);

      setDocumentError("");

      setUploadSuccess("");



      const response = await apiFetch(

        `/documents/${documentId}`,

        {

          method: "DELETE",

        }

      );



      if (!response.ok) {

        throw new Error(

          "Failed to delete document"

        );

      }



      if (

        selectedDocumentId === documentId

      ) {

        setSelectedDocumentId(null);

      }



      await loadDocuments();



      setMessages([]);



      await startConversation();

    } catch (error) {

      console.error(

        "Delete failed:",

        error

      );



      setDocumentError(

        "Could not delete the document."

      );

    } finally {

      setDeletingDocumentId(null);

    }

  }



  // ===================================

  // SOURCES

  // ===================================



  function buildSources(

    retrieval: RetrievalItem[]

  ): ChatSource[] {

    const uniqueSources =

      new Map<string, ChatSource>();



    retrieval.forEach((item) => {

      const document = documents.find(

        (doc) =>

          doc.id === item.document_id

      );



      const filename =

        document?.filename ??

        `Document ${item.document_id}`;



      const key =

        `${item.document_id}-${item.page_number}`;



      if (!uniqueSources.has(key)) {

        uniqueSources.set(key, {

          filename,

          page_number:

            item.page_number,

          chunk_index:

            item.chunk_index,

          similarity:

            item.similarity,

        });

      }

    });



    return Array.from(

      uniqueSources.values()

    );

  }



  // ===================================

  // SEND QUESTION

  // ===================================



  async function sendQuestion() {

    const trimmedQuestion =

      question.trim();



    if (

      !trimmedQuestion ||

      sending

    ) {

      return;

    }



    if (documents.length === 0) {

      setMessages(

        (currentMessages) => [

          ...currentMessages,

          {

            role: "assistant",

            content:

              "Please upload a PDF before asking questions.",

          },

        ]

      );



      return;

    }



    setMessages(

      (currentMessages) => [

        ...currentMessages,

        {

          role: "user",

          content:

            trimmedQuestion,

        },

      ]

    );



    setQuestion("");

    setSending(true);

    setConversationError("");



    try {

      let activeConversationId =

        conversationId;



      if (!activeConversationId) {

        activeConversationId =

          await startConversation();

      }



      if (!activeConversationId) {

        throw new Error(

          "Conversation could not be created"

        );

      }



      const documentFilter =

        selectedDocumentId !== null

          ? `&document_id=${selectedDocumentId}`

          : "";



      const response = await apiFetch(

        `/conversations/${activeConversationId}/messages?question=${encodeURIComponent(

          trimmedQuestion

        )}${documentFilter}`,

        {

          method: "POST",

        }

      );



      if (!response.ok) {

        throw new Error(

          "Failed to get answer"

        );

      }



      const data = await response.json();



      const sources =

        buildSources(

          data.retrieval ?? []

        );



      setMessages(

        (currentMessages) => [

          ...currentMessages,

          {

            role: "assistant",

            content: data.answer,

            sources,

          },

        ]

      );



      await loadMetrics();

    } catch (error) {

      console.error(

        "Chat request failed:",

        error

      );



      setMessages(

        (currentMessages) => [

          ...currentMessages,

          {

            role: "assistant",

            content:

              "Could not connect to the AI backend.",

          },

        ]

      );

    } finally {

      setSending(false);

    }

  }



  async function newConversation() {

    setMessages([]);

    setQuestion("");



    await startConversation();

  }



  const successRate =

    metrics &&

    metrics.total_requests > 0

      ? Math.round(

          (metrics.successful_requests /

            metrics.total_requests) *

            100

        )

      : 0;



  // ===================================

  // AUTH LOADING SCREEN

  // ===================================



  if (authLoading) {

    return (

      <main className="flex min-h-screen items-center justify-center bg-slate-950 text-white">

        <div className="text-center">

          <p className="text-lg font-medium">

            Loading...

          </p>



          <p className="mt-2 text-sm text-slate-500">

            Checking your session

          </p>

        </div>

      </main>

    );

  }



  // ===================================

  // LOGIN / SIGN UP SCREEN

  // ===================================



  if (!user) {

    return (

      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white">

        <div className="w-full max-w-md">

          <div className="mb-8 text-center">

            <h1 className="text-3xl font-bold tracking-tight">

              Enterprise RAG

            </h1>



            <p className="mt-2 text-sm text-slate-400">

              Secure Knowledge Assistant

            </p>

          </div>



          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl sm:p-8">

            <div className="mb-6">

              <h2 className="text-2xl font-semibold">

                {authMode === "signin"

                  ? "Welcome back"

                  : "Create your account"}

              </h2>



              <p className="mt-2 text-sm text-slate-400">

                {authMode === "signin"

                  ? "Sign in to access your private knowledge base."

                  : "Create an account to start your private knowledge base."}

              </p>

            </div>



            <div className="mb-5 grid grid-cols-2 rounded-xl border border-slate-800 bg-slate-950 p-1">

              <button

                onClick={() => {

                  setAuthMode("signin");

                  setAuthError("");

                  setAuthMessage("");

                }}

                className={`rounded-lg px-4 py-2 text-sm font-medium transition ${

                  authMode === "signin"

                    ? "bg-blue-600 text-white"

                    : "text-slate-400 hover:text-white"

                }`}

              >

                Sign In

              </button>



              <button

                onClick={() => {

                  setAuthMode("signup");

                  setAuthError("");

                  setAuthMessage("");

                }}

                className={`rounded-lg px-4 py-2 text-sm font-medium transition ${

                  authMode === "signup"

                    ? "bg-blue-600 text-white"

                    : "text-slate-400 hover:text-white"

                }`}

              >

                Sign Up

              </button>

            </div>



            <div className="space-y-4">

              <div>

                <label className="mb-2 block text-sm text-slate-300">

                  Email

                </label>



                <input

                  type="email"

                  value={email}

                  onChange={(event) =>

                    setEmail(

                      event.target.value

                    )

                  }

                  placeholder="you@company.com"

                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none transition placeholder:text-slate-600 focus:border-blue-500"

                />

              </div>



              <div>

                <label className="mb-2 block text-sm text-slate-300">

                  Password

                </label>



                <input

                  type="password"

                  value={password}

                  onChange={(event) =>

                    setPassword(

                      event.target.value

                    )

                  }

                  onKeyDown={(event) => {

                    if (

                      event.key === "Enter"

                    ) {

                      handleAuth();

                    }

                  }}

                  placeholder="••••••••"

                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none transition placeholder:text-slate-600 focus:border-blue-500"

                />

              </div>



              {authError && (

                <div className="rounded-xl border border-red-900 bg-red-950/30 p-3">

                  <p className="text-sm text-red-400">

                    {authError}

                  </p>

                </div>

              )}



              {authMessage && (

                <div className="rounded-xl border border-emerald-900 bg-emerald-950/30 p-3">

                  <p className="text-sm text-emerald-400">

                    {authMessage}

                  </p>

                </div>

              )}



              <button

                onClick={handleAuth}

                disabled={

                  authSubmitting ||

                  !email.trim() ||

                  !password.trim()

                }

                className="w-full rounded-xl bg-blue-600 px-4 py-3 font-medium transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"

              >

                {authSubmitting

                  ? "Please wait..."

                  : authMode ===

                      "signin"

                    ? "Sign In"

                    : "Create Account"}

              </button>

            </div>



            <div className="mt-6 border-t border-slate-800 pt-5 text-center">

              <p className="text-xs text-slate-500">

                Your documents and conversations will be isolated to your account.

              </p>

            </div>

          </div>

        </div>

      </main>

    );

  }



  // ===================================

  // AUTHENTICATED RAG DASHBOARD

  // ===================================



  return (

    <main className="min-h-screen bg-slate-950 text-white">

      <div className="mx-auto w-full max-w-[1700px] px-4 py-5 sm:px-6 lg:px-8">

        {/* HEADER */}

        <header className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">

          <div>

            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl lg:text-4xl">

              Enterprise RAG Knowledge Assistant

            </h1>



            <p className="mt-2 max-w-3xl text-sm text-slate-400 sm:text-base">

              Upload company documents, ask grounded questions, and monitor RAG performance.

            </p>

          </div>



          {/* USER */}

          <div className="flex items-center gap-3">

            <div className="text-right">

              <p className="text-xs text-slate-500">

                Signed in as

              </p>



              <p className="max-w-[220px] truncate text-sm text-slate-300">

                {user.email}

              </p>

            </div>



            <button

              onClick={handleLogout}

              className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300 transition hover:bg-slate-800"

            >

              Logout

            </button>

          </div>

        </header>



        <div className="grid gap-4 lg:grid-cols-12">

          {/* DOCUMENTS */}

          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-4 sm:p-5 lg:col-span-3">

            <div>

              <h2 className="text-lg font-semibold">

                Documents

              </h2>



              <p className="mt-1 text-sm text-slate-400">

                Manage your knowledge base

              </p>

            </div>



            <div className="mt-5">

              <label

                className={`block w-full rounded-xl bg-blue-600 px-4 py-3 text-center text-sm font-medium transition sm:text-base ${

                  uploading

                    ? "cursor-not-allowed opacity-60"

                    : "cursor-pointer hover:bg-blue-500"

                }`}

              >

                {uploading

                  ? "Uploading..."

                  : "+ Upload PDF"}



                <input

                  type="file"

                  accept="application/pdf"

                  className="hidden"

                  disabled={uploading}

                  onChange={(event) => {

                    const file =

                      event.target.files?.[0];



                    if (file) {

                      uploadDocument(file);

                    }



                    event.target.value = "";

                  }}

                />

              </label>



              {uploadError && (

                <div className="mt-3 rounded-xl border border-red-900 bg-red-950/30 p-3">

                  <p className="text-sm text-red-400">

                    {uploadError}

                  </p>

                </div>

              )}



              {uploadSuccess && (

                <div className="mt-3 rounded-xl border border-emerald-900 bg-emerald-950/30 p-3">

                  <p className="text-sm text-emerald-400">

                    {uploadSuccess}

                  </p>

                </div>

              )}

            </div>



            <div className="mt-5 max-h-[620px] space-y-3 overflow-y-auto pr-1">

              {loadingDocuments && (

                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">

                  <p className="text-sm text-slate-400">

                    Loading documents...

                  </p>

                </div>

              )}



              {!loadingDocuments &&

                documentError && (

                  <div className="rounded-xl border border-red-900 bg-red-950/30 p-4">

                    <p className="text-sm text-red-400">

                      {documentError}

                    </p>

                  </div>

                )}



              {!loadingDocuments &&

                !documentError &&

                documents.length === 0 && (

                  <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">

                    <p className="text-sm text-slate-400">

                      No documents uploaded yet.

                    </p>

                  </div>

                )}



              {documents.map((document) => (

                <div

                  key={document.id}

                  className={`rounded-xl border p-4 ${

                    selectedDocumentId ===

                    document.id

                      ? "border-blue-500 bg-blue-950/20"

                      : "border-slate-800 bg-slate-950"

                  }`}

                >

                  <p className="break-all text-sm font-medium sm:text-base">

                    {document.filename}

                  </p>



                  <p className="mt-2 text-xs text-slate-500">

                    {document.file_type} ·{" "}

                    {document.status}

                  </p>



                  <p className="mt-1 text-xs text-slate-600">

                    ID: {document.id}

                  </p>



                  <button

                    onClick={() =>

                      setSelectedDocumentId(

                        document.id

                      )

                    }

                    className="mt-3 w-full rounded-lg border border-blue-900 bg-blue-950/20 px-3 py-2 text-sm font-medium text-blue-400 transition hover:bg-blue-950/40"

                  >

                    {selectedDocumentId ===

                    document.id

                      ? "Selected"

                      : "Use this PDF"}

                  </button>



                  <button

                    onClick={() =>

                      deleteDocument(

                        document.id

                      )

                    }

                    disabled={

                      deletingDocumentId ===

                      document.id

                    }

                    className="mt-2 w-full rounded-lg border border-red-900 bg-red-950/30 px-3 py-2 text-sm font-medium text-red-400 transition hover:bg-red-950/60 disabled:cursor-not-allowed disabled:opacity-50"

                  >

                    {deletingDocumentId ===

                    document.id

                      ? "Deleting..."

                      : "Delete"}

                  </button>

                </div>

              ))}

            </div>

          </section>



          {/* AI CHAT */}

          <section className="flex min-h-[520px] flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 sm:min-h-[620px] lg:col-span-6 lg:min-h-[720px]">

            <div className="border-b border-slate-800 p-4 sm:p-5">

              <div className="flex items-center justify-between gap-4">

                <div>

                  <h2 className="text-lg font-semibold">

                    AI Assistant

                  </h2>



                  <p className="mt-1 text-sm text-slate-400">

                    Ask questions about your company documents

                  </p>



                  {conversationId && (

                    <p className="mt-1 text-xs text-slate-600">

                      Conversation #

                      {conversationId}

                    </p>

                  )}

                </div>



                <button

                  onClick={newConversation}

                  className="shrink-0 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-300 transition hover:bg-slate-800 sm:text-sm"

                >

                  New Chat

                </button>

              </div>



              <div className="mt-4">

                <label className="mb-2 block text-xs font-medium text-slate-400">

                  Search in

                </label>



                <select

                  value={

                    selectedDocumentId ===

                    null

                      ? "all"

                      : String(

                          selectedDocumentId

                        )

                  }

                  onChange={(event) => {

                    const value =

                      event.target.value;



                    if (value === "all") {

                      setSelectedDocumentId(

                        null

                      );

                    } else {

                      setSelectedDocumentId(

                        Number(value)

                      );

                    }



                    setMessages([]);

                    startConversation();

                  }}

                  disabled={

                    documents.length === 0

                  }

                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition focus:border-blue-500 disabled:cursor-not-allowed disabled:opacity-50"

                >

                  <option value="all">

                    All Documents

                  </option>



                  {documents.map(

                    (document) => (

                      <option

                        key={document.id}

                        value={document.id}

                      >

                        {

                          document.filename

                        }

                      </option>

                    )

                  )}

                </select>



                <p className="mt-2 text-xs text-slate-500">

                  {selectedDocumentId ===

                  null

                    ? "Searching across all uploaded PDFs."

                    : "Searching only the selected PDF."}

                </p>

              </div>

            </div>



            {conversationError && (

              <div className="border-b border-red-900 bg-red-950/20 px-4 py-3">

                <p className="text-sm text-red-400">

                  {conversationError}

                </p>

              </div>

            )}



            <div className="flex-1 space-y-5 overflow-y-auto p-4 sm:p-6">

              {messages.length === 0 &&

                !sending && (

                  <div className="flex h-full min-h-[300px] items-center justify-center">

                    <div className="text-center">

                      <p className="text-base font-medium text-slate-300">

                        Ask your knowledge base anything

                      </p>



                      <p className="mt-2 text-sm text-slate-500">

                        This conversation remembers your previous messages.

                      </p>

                    </div>

                  </div>

                )}



              {messages.map(

                (message, index) => {

                  if (

                    message.role ===

                    "user"

                  ) {

                    return (

                      <div

                        key={index}

                        className="ml-auto w-fit max-w-[90%] rounded-2xl bg-blue-600 px-4 py-3 text-sm leading-6 sm:max-w-[75%] sm:text-base"

                      >

                        {

                          message.content

                        }

                      </div>

                    );

                  }



                  return (

                    <div

                      key={index}

                      className="w-fit max-w-[95%] rounded-2xl bg-slate-800 p-4 text-sm leading-6 sm:max-w-[85%] sm:text-base"

                    >

                      <p>

                        {

                          message.content

                        }

                      </p>



                      {message.sources &&

                        message.sources

                          .length >

                          0 && (

                          <div className="mt-4 space-y-2">

                            {message.sources.map(

                              (

                                source,

                                sourceIndex

                              ) => (

                                <div

                                  key={`${source.filename}-${source.page_number}-${sourceIndex}`}

                                  className="rounded-lg border border-slate-700 bg-slate-950 p-3 text-xs text-slate-400"

                                >

                                  <p className="break-words">

                                    Source:{" "}

                                    {

                                      source.filename

                                    }{" "}

                                    · Page{" "}

                                    {

                                      source.page_number

                                    }

                                  </p>



                                  <p className="mt-1 text-slate-600">

                                    Similarity:{" "}

                                    {source.similarity.toFixed(

                                      4

                                    )}

                                  </p>

                                </div>

                              )

                            )}

                          </div>

                        )}

                    </div>

                  );

                }

              )}



              {sending && (

                <div className="w-fit rounded-2xl bg-slate-800 px-4 py-3 text-sm text-slate-400">

                  Thinking...

                </div>

              )}

            </div>



            <div className="border-t border-slate-800 p-3 sm:p-4">

              <div className="flex flex-col gap-3 sm:flex-row">

                <input

                  value={question}

                  onChange={(event) =>

                    setQuestion(

                      event.target.value

                    )

                  }

                  onKeyDown={(event) => {

                    if (

                      event.key ===

                      "Enter"

                    ) {

                      sendQuestion();

                    }

                  }}

                  disabled={sending}

                  placeholder="Ask a question about your documents..."

                  className="min-w-0 flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none transition placeholder:text-slate-500 focus:border-blue-500 disabled:cursor-not-allowed disabled:opacity-60 sm:text-base"

                />



                <button

                  onClick={sendQuestion}

                  disabled={

                    sending ||

                    !question.trim()

                  }

                  className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto sm:text-base"

                >

                  {sending

                    ? "Sending..."

                    : "Send"}

                </button>

              </div>

            </div>

          </section>



          {/* METRICS */}

          <section className="rounded-2xl border border-slate-800 bg-slate-900 p-4 sm:p-5 lg:col-span-3">

            <div>

              <h2 className="text-lg font-semibold">

                RAG Metrics

              </h2>



              <p className="mt-1 text-sm text-slate-400">

                System performance

              </p>

            </div>



            <div className="mt-5">

              {loadingMetrics && (

                <p className="text-sm text-slate-400">

                  Loading metrics...

                </p>

              )}



              {!loadingMetrics &&

                metricsError && (

                  <div className="rounded-xl border border-red-900 bg-red-950/30 p-4">

                    <p className="text-sm text-red-400">

                      {metricsError}

                    </p>

                  </div>

                )}



              {!loadingMetrics &&

                !metricsError &&

                metrics && (

                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-1">

                    <MetricCard

                      title="Total Requests"

                      value={String(

                        metrics.total_requests

                      )}

                    />



                    <MetricCard

                      title="Success Rate"

                      value={`${successRate}%`}

                    />



                    <MetricCard

                      title="Average Latency"

                      value={`${(

                        metrics.average_total_latency_ms /

                        1000

                      ).toFixed(

                        2

                      )} sec`}

                    />



                    <MetricCard

                      title="Avg Similarity"

                      value={metrics.average_top_similarity.toFixed(

                        4

                      )}

                    />

                  </div>

                )}

            </div>

          </section>

        </div>

      </div>

    </main>

  );

}



function MetricCard({

  title,

  value,

}: {

  title: string;

  value: string;

}) {

  return (

    <div className="min-w-0 rounded-xl border border-slate-800 bg-slate-950 p-4">

      <p className="text-xs text-slate-400 sm:text-sm">

        {title}

      </p>



      <p className="mt-2 break-words text-xl font-semibold sm:text-2xl">

        {value}

      </p>

    </div>

  );

}

