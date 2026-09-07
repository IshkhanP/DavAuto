import React, { useEffect, useRef, useState } from "react";
import { messagingService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { EmptyState, ErrorState, LoadingBlock } from "@/components/States";
import { formatDateTime, timeAgo } from "@/utils/format";
import { useAuth } from "@/context/AuthContext";
import type { Conversation, Message } from "@/types";

export const DashboardMessagesPage: React.FC = () => {
  const { user } = useAuth();
  const [selected, setSelected] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const messagesEnd = useRef<HTMLDivElement>(null);

  const { data: conversations, loading, error, reload } = useAsync<Conversation[]>(
    () => messagingService.list(),
    []
  );

  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    if (selected) {
      messagingService.listMessages(selected).then(setMessages);
      messagingService.markRead(selected).catch(() => {});
    }
  }, [selected]);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!selected || !draft.trim()) return;
    try {
      setSending(true);
      const m = await messagingService.sendMessage(selected, draft);
      setMessages((prev) => [...prev, m]);
      setDraft("");
    } catch {
      // ignore
    } finally {
      setSending(false);
    }
  };

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorState onRetry={reload} />;

  return (
    <div>
      <h1 style={{ marginBottom: 8 }}>Messages</h1>
      <p className="text-sm muted" style={{ marginBottom: 16 }}>Talk to sellers and dealers.</p>

      {(conversations ?? []).length === 0 ? (
        <EmptyState title="No conversations" description="Reach out to start chatting with sellers about their listings." />
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: 16, height: "70vh" }} className="msg-layout">
          <div className="card" style={{ overflowY: "auto" }}>
            {(conversations ?? []).map((c) => {
              const other = c.participants.find((p) => p.user_id !== user?.id);
              return (
                <button
                  key={c.id}
                  onClick={() => setSelected(c.id)}
                  style={{
                    width: "100%", textAlign: "left",
                    padding: 14, borderBottom: "1px solid var(--color-border)",
                    background: selected === c.id ? "var(--color-bg-soft)" : "#fff",
                    display: "flex", flexDirection: "column", gap: 4,
                  }}
                >
                  <div className="row-between">
                    <div style={{ fontWeight: 700 }}>{other?.full_name || "Conversation"}</div>
                    {c.unread_count > 0 && <span className="badge badge-red">{c.unread_count}</span>}
                  </div>
                  <div className="text-sm muted" style={{
                    display: "-webkit-box", WebkitLineClamp: 1, WebkitBoxOrient: "vertical", overflow: "hidden",
                  }}>
                    {c.last_message?.body || c.subject || "—"}
                  </div>
                  <div className="text-sm muted">{timeAgo(c.last_message_at || c.created_at)}</div>
                </button>
              );
            })}
          </div>

          <div className="card" style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
            {!selected ? (
              <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--color-text-muted)" }}>
                Select a conversation to start reading
              </div>
            ) : (
              <>
                <div style={{ padding: 14, borderBottom: "1px solid var(--color-border)", fontWeight: 700 }}>
                  {conversations?.find((c) => c.id === selected)?.subject || "Conversation"}
                </div>
                <div style={{ flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>
                  {messages.map((m) => {
                    const mine = m.sender_id === user?.id;
                    return (
                      <div key={m.id} style={{
                        alignSelf: mine ? "flex-end" : "flex-start",
                        maxWidth: "70%",
                        background: mine ? "var(--color-black)" : "var(--color-light-gray)",
                        color: mine ? "#fff" : "var(--color-text)",
                        padding: "10px 14px", borderRadius: 14,
                      }}>
                        <div style={{ whiteSpace: "pre-wrap" }}>{m.body}</div>
                        <div style={{ fontSize: 11, opacity: 0.7, marginTop: 4 }}>{formatDateTime(m.created_at)}</div>
                      </div>
                    );
                  })}
                  <div ref={messagesEnd} />
                </div>
                <div style={{ padding: 12, borderTop: "1px solid var(--color-border)", display: "flex", gap: 8 }}>
                  <input
                    className="input"
                    placeholder="Type a message..."
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                  />
                  <button className="btn btn-blue" onClick={send} disabled={sending || !draft.trim()}>Send</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      <style>{`
        @media (max-width: 800px) {
          .msg-layout { grid-template-columns: 1fr !important; height: auto !important; }
        }
      `}</style>
    </div>
  );
};