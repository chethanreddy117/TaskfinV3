"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import {
  SignedIn,
  SignedOut,
  SignInButton,
  UserButton,
  useAuth,
  useUser
} from "@clerk/nextjs";

type Message = {
  role: "user" | "assistant";
  content: string;
};

const API_base = process.env.NEXT_PUBLIC_API_BASE

  // || "http://localhost:8000/api/v1";
// const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;
// if (!API) {
//   throw new Error("NEXT_PUBLIC_API_BASE_URL is not defined");
// }
const API = `${API_base}/api/v1`;

export default function Home() {
  const { getToken, isLoaded: authLoaded } = useAuth();
  const { user, isLoaded: userLoaded } = useUser();

  // ---------------- Chat ----------------
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingAction, setLoadingAction] = useState("");

  // ---------------- Confirmation ----------------
  const [awaitingConfirm, setAwaitingConfirm] = useState(false);
  const [expiresAt, setExpiresAt] = useState<number | null>(null);
  const [remaining, setRemaining] = useState<number | null>(null);

  useEffect(() => {
    console.log("---------------- DEBUG ----------------");
    console.log("Raw Env Var:", process.env.NEXT_PUBLIC_API_BASE);
    console.log("Final API URL:", API);
    console.log("---------------------------------------");
  }, []);

  // ---------------- Timer ----------------
  useEffect(() => {
    if (!awaitingConfirm || !expiresAt) return;

    const id = setInterval(() => {
      const left = Math.max(
        0,
        Math.floor((expiresAt - Date.now()) / 1000)
      );
      setRemaining(left);

      if (left === 0) {
        setAwaitingConfirm(false);
        setExpiresAt(null);
        setRemaining(null);

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "⛔ Payment confirmation expired. Payment cancelled.",
          },
        ]);
      }
    }, 1000);

    return () => clearInterval(id);
  }, [awaitingConfirm, expiresAt]);

  // ---------------- Quick Actions ----------------
  const quickActions = [
    { label: "📋 Show Bills", message: "show my bills" },
    { label: "💰 Check Balance", message: "show balance" },
    { label: "📜 History", message: "show history" },
    { label: "📊 My Limits", message: "show my limits" },
  ];

  const sendQuickAction = (message: string) => {
    if (loading || awaitingConfirm) return;
    setInput(message);
    const form = document.querySelector("form");
    if (form) {
      form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
    }
  };

  // ---------------- Chat Submit ----------------
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const text = input.trim();
    const lower = text.toLowerCase();
    setInput("");

    if (awaitingConfirm && lower !== "yes" && lower !== "no") {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: text },
        {
          role: "assistant",
          content:
            "Please confirm the payment by replying **yes** or **no**.\\n_This request will expire automatically._",
        },
      ]);
      return;
    }

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    if (lower.includes("bill")) {
      setLoadingAction("Checking bills");
    } else if (lower.includes("balance")) {
      setLoadingAction("Fetching balance");
    } else if (lower.includes("history")) {
      setLoadingAction("Loading history");
    } else if (lower.includes("pay")) {
      setLoadingAction("Processing payment");
    } else {
      setLoadingAction("Thinking");
    }

    try {
      const token = await getToken();
      const res = await axios.post(
        `${API}/agent/chat`,
        { message: text },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const reply: string = res.data.response;
      const replyLower = reply.toLowerCase();

      if (
        (replyLower.includes("do you want to pay") ||
          replyLower.includes("confirm payment")) &&
        replyLower.includes("yes/no")
      ) {
        setAwaitingConfirm(true);
        setExpiresAt(Date.now() + 60000);
        setRemaining(60);
      }

      if (
        replyLower.includes("payment cancelled") ||
        replyLower.includes("payment successful") ||
        replyLower.includes("expired")
      ) {
        setAwaitingConfirm(false);
        setExpiresAt(null);
        setRemaining(null);
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: reply },
      ]);
    } catch (error: any) {
      let errorMessage = "Error communicating with backend.";

      if (error.response?.status === 401) {
        errorMessage = "Session expired or unauthorized. Please ensure you are logged in.";
      } else if (error.code === "ERR_NETWORK") {
        errorMessage = "Cannot connect to server. Please check your connection and ensure the backend is running.";
      } else if (error.response?.data?.detail) {
        errorMessage = `Error: ${error.response.data.detail}`;
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `❌ ${errorMessage}`,
        },
      ]);
    } finally {
      setLoading(false);
      setLoadingAction("");
    }
  };

  if (!authLoaded || !userLoaded) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </main>
    );
  }

  return (
    <>
      <SignedIn>
        <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
          <div className="w-full max-w-4xl h-[85vh] bg-white rounded-2xl shadow-2xl flex flex-col">
            {/* Header */}
            <div className="px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-t-2xl flex justify-between items-center">
              <div>
                <h1 className="text-xl font-bold">TaskFin</h1>
                <p className="text-xs opacity-90">
                  AI Bill Payment Assistant
                </p>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs opacity-90">Hi, {user?.firstName || "User"}</span>
                <UserButton afterSignOutUrl="/" />
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">👋</div>
                  <h2 className="text-2xl font-semibold text-gray-800 mb-2">
                    Welcome to TaskFin!
                  </h2>
                  <p className="text-gray-600 mb-6">
                    I can help you manage and pay your bills. Try the quick actions below or ask me anything!
                  </p>
                </div>
              )}

              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                >
                  <div
                    className={`max-w-[80%] px-5 py-3 rounded-2xl text-sm shadow-sm ${msg.role === "user"
                      ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white"
                      : "bg-gray-50 text-gray-900 border border-gray-200"
                      }`}
                  >
                    <span className="whitespace-pre-line">{msg.content}</span>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex items-center gap-2 text-gray-500 text-sm">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                    <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                    <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                  </div>
                  <span className="italic">{loadingAction}...</span>
                </div>
              )}
            </div>

            {/* Global Timer */}
            {awaitingConfirm && remaining !== null && (
              <div className="text-center bg-yellow-50 border-t border-yellow-200 py-3">
                <p className="text-sm text-yellow-800 font-medium">
                  ⏳ Confirmation expires in {remaining} seconds
                </p>
              </div>
            )}

            {/* Quick Actions */}
            {!awaitingConfirm && (
              <div className="px-6 py-3 border-t border-gray-200 bg-gray-50">
                <div className="flex flex-wrap gap-2">
                  {quickActions.map((action, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendQuickAction(action.message)}
                      disabled={loading}
                      className="px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-indigo-50 hover:border-indigo-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <form
              onSubmit={handleSubmit}
              className="p-4 border-t border-gray-200 flex gap-3 bg-white rounded-b-2xl"
            >
              <input
                className="flex-1 px-5 py-3 bg-gray-50 text-gray-900 rounded-xl border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                placeholder={awaitingConfirm ? "Type 'yes' or 'no'..." : "Ask about your bills…"}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
              />
              <button
                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 px-6 rounded-xl text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
                disabled={loading}
              >
                {loading ? "..." : "Send"}
              </button>
            </form>
          </div>
        </main>
      </SignedIn>
      <SignedOut>
        <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-600 p-4">
          <div className="bg-white p-8 rounded-2xl w-96 shadow-2xl text-center">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">TaskFin</h1>
            <p className="text-sm text-gray-500 mb-8">Agent-Based Bill Payment</p>
            <SignInButton mode="modal">
              <button className="w-full bg-indigo-600 hover:bg-indigo-700 py-3 rounded-lg text-white font-medium transition-colors">
                Sign In to Continue
              </button>
            </SignInButton>
          </div>
        </main>
      </SignedOut>
    </>
  );
}
