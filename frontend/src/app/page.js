"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [calendar, setCalendar] = useState([]);
  
  // Dashboard Widget states
  const [books, setBooks] = useState([]);
  const [bookQuery, setBookQuery] = useState("");
  const [borrowModalBook, setBorrowModalBook] = useState(null);
  const [borrowDueDate, setBorrowDueDate] = useState("");
  const [borrowError, setBorrowError] = useState("");

  const [menu, setMenu] = useState(null);
  const [selectedMenuDay, setSelectedMenuDay] = useState("today");

  const [events, setEvents] = useState([]);
  const [eventQuery, setEventQuery] = useState("");
  const [eventStartDate, setEventStartDate] = useState("");
  const [eventEndDate, setEventEndDate] = useState("");

  const [pdfs, setPdfs] = useState([]);
  const [pdfQuery, setPdfQuery] = useState("");
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadSubject, setUploadSubject] = useState("");
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [uploadLoading, setUploadLoading] = useState(false);

  // Chat State
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([
    {
      sender: "ai",
      text: "Hello! I am your Campus Assistant. Ask me anything about Library books, Cafeteria menus, Club events, or Academic PDFs. I can also help cross-reference items with your calendar!"
    }
  ]);
  const [chatLoading, setChatLoading] = useState(false);
  const [highlightedWidgets, setHighlightedWidgets] = useState([]);

  const messagesEndRef = useRef(null);

  // Auth Guard
  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      router.push("/login");
    } else {
      setToken(storedToken);
      fetchInitialData(storedToken);
    }
  }, [router]);

  // Scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, chatLoading]);

  const fetchInitialData = async (authToken) => {
    try {
      const headers = { Authorization: `Bearer ${authToken}` };
      
      // Fetch Profile
      const profileRes = await fetch(`${API_BASE_URL}/profile/me`, { headers });
      if (!profileRes.ok) throw new Error("Auth failed");
      const profileData = await profileRes.json();
      setProfile(profileData);
      setUser(profileData);

      // Fetch Calendar
      fetchCalendar(authToken);

      // Fetch Books
      fetchBooks(authToken, "");

      // Fetch Menu
      fetchMenu(authToken, "today");

      // Fetch Events
      fetchEvents(authToken, "", "", "");

      // Fetch PDFs
      fetchPdfs(authToken, "");

    } catch (err) {
      console.error(err);
      localStorage.removeItem("token");
      router.push("/login");
    }
  };

  const refreshProfileAndCalendar = async (authToken) => {
    try {
      const headers = { Authorization: `Bearer ${authToken}` };
      const profileRes = await fetch(`${API_BASE_URL}/profile/me`, { headers });
      if (profileRes.ok) {
        const profileData = await profileRes.json();
        setProfile(profileData);
        setUser(profileData);
      }
      fetchCalendar(authToken);
    } catch (err) {
      console.error(err);
    }
  };

  // --- API Fetch Helpers ---
  const fetchCalendar = async (authToken) => {
    const res = await fetch(`${API_BASE_URL}/profile/calendar`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (res.ok) {
      const data = await res.json();
      setCalendar(data);
    }
  };

  const fetchBooks = async (authToken, query) => {
    const url = query 
      ? `${API_BASE_URL}/mcp/library/search?q=${encodeURIComponent(query)}`
      : `${API_BASE_URL}/mcp/library/books`;
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (res.ok) {
      const data = await res.json();
      setBooks(data);
    }
  };

  const fetchMenu = async (authToken, day) => {
    const res = await fetch(`${API_BASE_URL}/mcp/cafeteria/menu/${day}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (res.ok) {
      const data = await res.json();
      setMenu(data);
    }
  };

  const fetchEvents = async (authToken, query, start, end) => {
    let url = `${API_BASE_URL}/mcp/events/all`;
    if (query) {
      url = `${API_BASE_URL}/mcp/events/search?q=${encodeURIComponent(query)}`;
    } else if (start || end) {
      url = `${API_BASE_URL}/mcp/events/list?`;
      if (start) url += `start_date=${start}&`;
      if (end) url += `end_date=${end}`;
    }
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (res.ok) {
      const data = await res.json();
      setEvents(data);
    }
  };

  const fetchPdfs = async (authToken, query) => {
    const url = query
      ? `${API_BASE_URL}/mcp/academics/search?q=${encodeURIComponent(query)}`
      : `${API_BASE_URL}/mcp/academics/pdfs`;
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (res.ok) {
      const data = await res.json();
      setPdfs(data);
    }
  };

  // --- Handlers ---
  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  const handleBookSearch = (e) => {
    setBookQuery(e.target.value);
    fetchBooks(token, e.target.value);
  };

  const handleOpenBorrowModal = (book) => {
    setBorrowModalBook(book);
    // Set default due date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setBorrowDueDate(tomorrow.toISOString().split("T")[0]);
    setBorrowError("");
  };

  const handleBorrowSubmit = async (e) => {
    e.preventDefault();
    setBorrowError("");
    try {
      const res = await fetch(`${API_BASE_URL}/profile/books`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          book_id: borrowModalBook.id,
          title: borrowModalBook.title,
          due_date: borrowDueDate,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to borrow book.");
      }
      
      // Success: Close and refresh profile, calendar, and books
      setBorrowModalBook(null);
      await refreshProfileAndCalendar(token);
      fetchBooks(token, bookQuery);
    } catch (err) {
      setBorrowError(err.message);
    }
  };

  const handleReturnBook = async (bookId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/profile/books/${bookId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        await refreshProfileAndCalendar(token);
        fetchBooks(token, bookQuery);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleMenuDayChange = (day) => {
    setSelectedMenuDay(day);
    fetchMenu(token, day);
  };

  const handleLikeMenuDay = async (day) => {
    try {
      const res = await fetch(`${API_BASE_URL}/profile/cafeteria`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ day }),
      });
      if (res.ok) {
        await refreshProfileAndCalendar(token);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleEventSearch = (e) => {
    setEventQuery(e.target.value);
    setEventStartDate("");
    setEventEndDate("");
    fetchEvents(token, e.target.value, "", "");
  };

  const handleEventDateFilter = (start, end) => {
    setEventQuery("");
    fetchEvents(token, "", start, end);
  };

  const handleToggleEventFlag = async (eventId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/profile/events`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ event_id: eventId }),
      });
      if (res.ok) {
        await refreshProfileAndCalendar(token);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handlePdfSearch = (e) => {
    setPdfQuery(e.target.value);
    fetchPdfs(token, e.target.value);
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    setUploadError("");
    if (!uploadFile) {
      setUploadError("Please select a PDF file.");
      return;
    }
    if (uploadFile.size > 20 * 1024 * 1024) {
      setUploadError("File exceeds 20MB limit.");
      return;
    }

    setUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append("title", uploadTitle);
      formData.append("subject", uploadSubject);
      formData.append("file", uploadFile);

      const res = await fetch(`${API_BASE_URL}/mcp/academics/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to upload file.");
      }

      setUploadModalOpen(false);
      setUploadTitle("");
      setUploadSubject("");
      setUploadFile(null);
      fetchPdfs(token, "");
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploadLoading(false);
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = chatInput.trim();
    setChatHistory((prev) => [...prev, { sender: "user", text: userMessage }]);
    setChatInput("");
    setChatLoading(true);
    setHighlightedWidgets([]); // Clear previous highlights

    try {
      const res = await fetch(`${API_BASE_URL}/ai/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ query: userMessage }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to communicate with AI.");
      }

      setChatHistory((prev) => [...prev, { sender: "ai", text: data.response }]);
      if (data.highlighted_widgets && data.highlighted_widgets.length > 0) {
        setHighlightedWidgets(data.highlighted_widgets);
      }
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        { sender: "ai", text: `Error: ${err.message || "Failed to fetch response."}` },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  // Helper check if book is currently borrowed by user
  const isBookBorrowed = (bookId) => {
    if (!profile) return false;
    return profile.borrowed_books.some((b) => b.book_id === bookId);
  };

  // Helper check if event is flagged
  const isEventFlaged = (eventId) => {
    if (!profile) return false;
    return profile.flagged_events.some((f) => f.event_id === eventId);
  };

  // Helper check if day is liked
  const isDayLiked = (day) => {
    if (!profile) return false;
    return profile.liked_menu_days.some((l) => l.day.toLowerCase() === day.toLowerCase());
  };

  if (!user || !profile) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" }}>
        <div className="typing-indicator">
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Main widgets area */}
      <main className="dashboard-main">
        <header className="dashboard-navbar">
          <div className="navbar-brand">
            <h1>Campus Intelligence</h1>
          </div>
          <div className="navbar-user">
            <span className="user-badge">{user.name} ({user.roll_number})</span>
            <button onClick={handleLogout} className="btn-logout">Logout</button>
          </div>
        </header>

        {/* Widgets Grid */}
        <div className="widget-grid">
          
          {/* Library Widget */}
          <section className={`widget-card ${highlightedWidgets.includes("library") ? "active-glow" : ""}`}>
            <header className="widget-header library-header">
              <h2>Library Catalog</h2>
              <input 
                type="text" 
                placeholder="Search title/author..." 
                className="form-input" 
                style={{ width: "180px", padding: "6px 10px", fontSize: "0.8rem" }}
                value={bookQuery}
                onChange={handleBookSearch}
              />
            </header>
            <div className="widget-content">
              {books.length === 0 ? (
                <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No books found.</p>
              ) : (
                <ul className="data-list">
                  {books.map((b) => (
                    <li key={b.id} className="data-item">
                      <div className="data-info">
                        <span className="data-title">{b.title}</span>
                        <span className="data-subtitle">{b.author} | {b.category}</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <span className={`data-badge ${b.available_copies > 0 ? "badge-available" : "badge-unavailable"}`}>
                          {b.available_copies > 0 ? `${b.available_copies} Left` : "Out of Stock"}
                        </span>
                        {isBookBorrowed(b.id) ? (
                          <button 
                            onClick={() => handleReturnBook(b.id)} 
                            className="btn-icon" 
                            style={{ width: "auto", padding: "0 10px", color: "var(--error)" }}
                            title="Return Book"
                          >
                            Return
                          </button>
                        ) : (
                          <button 
                            onClick={() => handleOpenBorrowModal(b)} 
                            className="btn-icon" 
                            style={{ width: "auto", padding: "0 10px" }}
                            disabled={b.available_copies === 0}
                            title="Borrow Book"
                          >
                            Borrow
                          </button>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          {/* Cafeteria Widget */}
          <section className={`widget-card ${highlightedWidgets.includes("cafeteria") ? "active-glow" : ""}`}>
            <header className="widget-header cafeteria-header" style={{ display: "block" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                <h2>Cafeteria Menu</h2>
                <button 
                  onClick={() => handleLikeMenuDay(menu?.day || "")} 
                  className="btn-icon" 
                  style={{ width: "auto", padding: "0 10px", color: isDayLiked(menu?.day || "") ? "var(--error)" : "var(--text-secondary)" }}
                >
                  {isDayLiked(menu?.day || "") ? "Liked" : "Like"}
                </button>
              </div>
              <div style={{ display: "flex", gap: "6px", overflowX: "auto", paddingBottom: "4px" }}>
                {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "today"].map((d) => (
                  <button 
                    key={d} 
                    onClick={() => handleMenuDayChange(d)} 
                    className="user-badge" 
                    style={{ 
                      cursor: "pointer", 
                      background: selectedMenuDay === d ? "var(--accent-primary)" : "rgba(255,255,255,0.05)",
                      color: selectedMenuDay === d ? "white" : "var(--text-primary)",
                      border: "none",
                      padding: "4px 10px"
                    }}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </header>
            <div className="widget-content">
              {menu ? (
                <div style={{ fontSize: "0.9rem", display: "flex", flexDirection: "column", gap: "10px" }}>
                  <div style={{ fontWeight: "600", color: "var(--accent-secondary)" }}>{menu.day} Menu</div>
                  <div><strong>Breakfast:</strong> {menu.breakfast}</div>
                  <div><strong>Lunch:</strong> {menu.lunch}</div>
                  <div><strong>Snacks:</strong> {menu.snacks}</div>
                  <div><strong>Dinner:</strong> {menu.dinner}</div>
                </div>
              ) : (
                <p>Loading menu...</p>
              )}
            </div>
          </section>

          {/* Events Widget */}
          <section className={`widget-card ${highlightedWidgets.includes("events") ? "active-glow" : ""}`}>
            <header className="widget-header events-header" style={{ display: "block" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                <h2>Campus Events</h2>
                <input 
                  type="text" 
                  placeholder="Search club/title..." 
                  className="form-input" 
                  style={{ width: "160px", padding: "6px 10px", fontSize: "0.8rem" }}
                  value={eventQuery}
                  onChange={handleEventSearch}
                />
              </div>
              <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                <input 
                  type="date" 
                  className="form-input" 
                  style={{ padding: "4px", fontSize: "0.75rem", background: "rgba(0,0,0,0.2)" }}
                  value={eventStartDate}
                  onChange={(e) => {
                    setEventStartDate(e.target.value);
                    handleEventDateFilter(e.target.value, eventEndDate);
                  }}
                />
                <span style={{ fontSize: "0.75rem" }}>to</span>
                <input 
                  type="date" 
                  className="form-input" 
                  style={{ padding: "4px", fontSize: "0.75rem", background: "rgba(0,0,0,0.2)" }}
                  value={eventEndDate}
                  onChange={(e) => {
                    setEventEndDate(e.target.value);
                    handleEventDateFilter(eventStartDate, e.target.value);
                  }}
                />
              </div>
            </header>
            <div className="widget-content">
              {events.length === 0 ? (
                <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No events found.</p>
              ) : (
                <ul className="data-list">
                  {events.map((e) => (
                    <li key={e.id} className="data-item">
                      <div className="data-info">
                        <span className="data-title">{e.title}</span>
                        <span className="data-subtitle">{e.club} | Location: {e.location}</span>
                        <span className="data-subtitle" style={{ color: "var(--accent-secondary)", fontSize: "0.75rem" }}>
                          Date: {e.date} at {e.time}
                        </span>
                      </div>
                      <button 
                        onClick={() => handleToggleEventFlag(e.id)} 
                        className="btn-icon"
                        style={{ width: "auto", padding: "0 10px", color: isEventFlaged(e.id) ? "var(--warning)" : "var(--text-secondary)" }}
                        title="Toggle Flag"
                      >
                        {isEventFlaged(e.id) ? "Unflag" : "Flag"}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          {/* Academics Widget */}
          <section className={`widget-card ${highlightedWidgets.includes("academics") ? "active-glow" : ""}`}>
            <header className="widget-header academics-header">
              <h2>Course Materials</h2>
              <div style={{ display: "flex", gap: "8px" }}>
                <input 
                  type="text" 
                  placeholder="Search materials..." 
                  className="form-input" 
                  style={{ width: "140px", padding: "6px 10px", fontSize: "0.8rem" }}
                  value={pdfQuery}
                  onChange={handlePdfSearch}
                />
                <button onClick={() => setUploadModalOpen(true)} className="btn-icon" title="Upload Material">+</button>
              </div>
            </header>
            <div className="widget-content">
              {pdfs.length === 0 ? (
                <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No course materials found.</p>
              ) : (
                <ul className="data-list">
                  {pdfs.map((p) => (
                    <li key={p.id} className="data-item">
                      <div className="data-info">
                        <span className="data-title">{p.title}</span>
                        <span className="data-subtitle">{p.subject} | Uploaded by {p.uploaded_by}</span>
                      </div>
                      <a 
                        href={`${API_BASE_URL}${p.file_url}`} 
                        download
                        className="btn-icon" 
                        style={{ textDecoration: "none", width: "auto", padding: "0 10px" }}
                        title="Download PDF"
                      >
                        Download
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

        </div>

        {/* Aggregated Calendar Section */}
        <section className={`widget-card ${highlightedWidgets.includes("calendar") ? "active-glow" : ""}`} style={{ minHeight: "auto", flexGrow: 1 }}>
          <header className="widget-header calendar-header">
            <h2>Personal Calendar & Schedule</h2>
          </header>
          <div className="widget-content" style={{ maxHeight: "none" }}>
            {calendar.length === 0 ? (
              <p style={{ color: "var(--text-muted)", textAlign: "center", padding: "20px 0" }}>
                Your calendar is empty. Borrow a book, flag a club event, or like a cafeteria day menu to add items!
              </p>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "16px" }}>
                {calendar.map((item, idx) => (
                  <div 
                    key={idx} 
                    className="data-item" 
                    style={{ 
                      flexDirection: "column", 
                      alignItems: "flex-start", 
                      gap: "6px",
                      borderLeft: `4px solid ${
                        item.type === "book_due" ? "var(--accent-primary)" : 
                        item.type === "event" ? "var(--accent-secondary)" : 
                        "var(--warning)"
                      }`
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", width: "100%" }}>
                      <span className="data-badge badge-date">{item.date}</span>
                      <span style={{ 
                        fontSize: "0.75rem", 
                        textTransform: "uppercase", 
                        letterSpacing: "0.05em",
                        color: "var(--text-secondary)"
                      }}>
                        {item.type.replace("_", " ")}
                      </span>
                    </div>
                    <span className="data-title" style={{ fontSize: "0.95rem" }}>{item.title}</span>
                    <span className="data-subtitle" style={{ fontSize: "0.8rem" }}>{item.description}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>

      {/* Persistent Chat Panel */}
      <aside className="chat-panel">
        <header className="chat-header">
          <div className="chat-logo">AI</div>
          <div className="chat-title">
            <h2>Campus Assistant</h2>
            <p>Ready to assist</p>
          </div>
          {highlightedWidgets.length > 0 && (
            <button 
              onClick={() => setHighlightedWidgets([])} 
              className="btn-logout" 
              style={{ marginLeft: "auto", fontSize: "0.75rem", padding: "4px 8px" }}
            >
              Clear Highlights
            </button>
          )}
        </header>

        <div className="chat-messages">
          {chatHistory.map((msg, idx) => (
            <div 
              key={idx} 
              className={`message-bubble ${msg.sender === "user" ? "message-user" : "message-ai"}`}
            >
              {msg.text}
            </div>
          ))}
          {chatLoading && (
            <div className="message-bubble message-ai" style={{ width: "fit-content" }}>
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <form onSubmit={handleChatSubmit} className="chat-form">
            <input 
              type="text" 
              placeholder="Ask me anything..." 
              className="chat-input"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={chatLoading}
            />
            <button type="submit" className="btn-send" disabled={chatLoading}>
              Send
            </button>
          </form>
        </div>
      </aside>

      {/* Borrow Book Modal */}
      {borrowModalBook && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">Borrow Book</h3>
              <button className="btn-close" onClick={() => setBorrowModalBook(null)}>&times;</button>
            </div>
            <form onSubmit={handleBorrowSubmit}>
              <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
                You are adding <strong>{borrowModalBook.title}</strong> to your borrowed books log.
              </p>
              <div className="form-group">
                <label className="form-label">Return Due Date</label>
                <input 
                  type="date" 
                  required 
                  className="form-input"
                  value={borrowDueDate}
                  onChange={(e) => setBorrowDueDate(e.target.value)}
                />
                {borrowError && <p className="error-message">{borrowError}</p>}
              </div>
              <div className="btn-group">
                <button type="button" className="btn-cancel" onClick={() => setBorrowModalBook(null)}>Cancel</button>
                <button type="submit" className="btn-submit">Confirm Borrow</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Course Material Modal */}
      {uploadModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="modal-title">Upload Course Material</h3>
              <button className="btn-close" onClick={() => setUploadModalOpen(false)}>&times;</button>
            </div>
            <form onSubmit={handleUploadSubmit}>
              <div className="form-group">
                <label className="form-label">Material Title</label>
                <input 
                  type="text" 
                  required 
                  placeholder="e.g. Intro to Computational Theory" 
                  className="form-input"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Subject / Course</label>
                <input 
                  type="text" 
                  required 
                  placeholder="e.g. Computer Science" 
                  className="form-input"
                  value={uploadSubject}
                  onChange={(e) => setUploadSubject(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Select PDF File (Max 20MB)</label>
                <input 
                  type="file" 
                  required 
                  accept=".pdf,application/pdf"
                  className="form-input"
                  onChange={(e) => setUploadFile(e.target.files[0])}
                />
                {uploadError && <p className="error-message">{uploadError}</p>}
              </div>
              <div className="btn-group">
                <button type="button" className="btn-cancel" onClick={() => setUploadModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn-submit" disabled={uploadLoading}>
                  {uploadLoading ? "Uploading..." : "Upload PDF"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
