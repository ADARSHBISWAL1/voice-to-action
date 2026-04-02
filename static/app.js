(function () {
  const API = "";

  const el = {
    btnListen: document.getElementById("btnListen"),
    btnLabel: document.getElementById("btnLabel"),
    btnSend: document.getElementById("btnSend"),
    textCmd: document.getElementById("textCmd"),
    transcript: document.getElementById("transcript"),
    result: document.getElementById("result"),
    micStatus: document.getElementById("micStatus"),
    serverStatus: document.getElementById("serverStatus"),
  };

  let recognition = null;
  let listening = false;
  let continuousListening = false;
  let activationWordDetected = false;
  /** @type {AbortController | null} */
  let commandAbort = null;

  function setMicBadge(text, className) {
    el.micStatus.textContent = text;
    el.micStatus.className = "badge " + className;
  }

  function speakResponse(text) {
    try {
      const synthesis = window.speechSynthesis;
      // Cancel any ongoing speech
      synthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9; // Slightly slower for better clarity
      utterance.pitch = 1.0;
      utterance.volume = 1.0; // Full volume
      
      // Get available voices and set a preferred one
      const voices = synthesis.getVoices();
      if (voices.length > 0) {
        // Prefer a female voice if available, otherwise use the default
        const femaleVoice = voices.find(voice => 
          voice.name.includes('Female') || 
          voice.name.includes('Samantha') || 
          voice.name.includes('Karen') ||
          voice.name.includes('Zira') ||
          voice.name.includes('Microsoft')
        );
        utterance.voice = femaleVoice || voices[0];
        console.log('Using voice:', utterance.voice.name);
      }
      
      synthesis.speak(utterance);
      console.log('Speaking:', text);
    } catch (error) {
      console.log('Speech synthesis error:', error);
    }
  }

  function setServerBadge(text, className) {
    el.serverStatus.textContent = text;
    el.serverStatus.className = "badge " + className;
  }

  async function checkHealth() {
    try {
      const r = await fetch(API + "/api/health", {
        method: "GET",
        cache: "no-store",
      });
      if (!r.ok) throw new Error("bad status");
      setServerBadge("Server connected", "badge-ok");
    } catch {
      setServerBadge("Server offline — run Python app", "badge-err");
    }
  }

  async function sendCommand(text) {
    const trimmed = (text || "").trim();
    el.transcript.textContent = trimmed || "—";
    el.result.textContent = "…";
    el.result.classList.remove("err");

    if (commandAbort) commandAbort.abort();
    commandAbort = new AbortController();

    try {
      // #region agent log
      fetch("http://127.0.0.1:7649/ingest/a41bbba2-c5de-40dc-b386-e8597c2bae63", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "5ce319",
        },
        body: JSON.stringify({
          sessionId: "5ce319",
          location: "app.js:sendCommand",
          message: "fetch_command_start",
          data: { text: trimmed },
          timestamp: Date.now(),
          hypothesisId: "E",
          runId: "pre-fix",
        }),
      }).catch(function () {});
      // #endregion
      const r = await fetch(API + "/api/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: trimmed }),
        signal: commandAbort.signal,
      });
      const data = await r.json();
      // #region agent log
      fetch("http://127.0.0.1:7649/ingest/a41bbba2-c5de-40dc-b386-e8597c2bae63", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "5ce319",
        },
        body: JSON.stringify({
          sessionId: "5ce319",
          location: "app.js:sendCommand",
          message: "fetch_command_done",
          data: {
            ok: data.ok,
            action: data.action,
            message: data.message,
            received: data.received,
            httpStatus: r.status,
          },
          timestamp: Date.now(),
          hypothesisId: "E",
          runId: "pre-fix",
        }),
      }).catch(function () {});
      // #endregion
      el.result.textContent = data.message || "(no message)";
      if (!data.ok) {
        el.result.classList.add("err");
        speakResponse("Sorry, I couldn't do that. Please try again.");
      } else {
        // Provide verbal feedback for successful commands
        if (data.action === "youtube" || data.action === "youtube_search") {
          speakResponse("Opening YouTube for you.");
        } else if (data.action === "app") {
          speakResponse("Launching application.");
        } else if (data.action === "website") {
          speakResponse("Opening website.");
        } else if (data.action === "chat") {
          speakResponse(data.message);
        } else if (data.action === "music") {
          speakResponse("Playing music.");
        } else if (data.action === "system") {
          speakResponse("System command executed.");
        } else if (data.action === "file") {
          speakResponse("Opening folder.");
        } else if (data.action === "search") {
          speakResponse("Searching the web.");
        } else if (data.action === "system_warning") {
          speakResponse("Please confirm this action.");
        } else {
          speakResponse("Done!");
        }
      }
    } catch (e) {
      // #region agent log
      fetch("http://127.0.0.1:7649/ingest/a41bbba2-c5de-40dc-b386-e8597c2bae63", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "5ce319",
        },
        body: JSON.stringify({
          sessionId: "5ce319",
          location: "app.js:sendCommand",
          message: "fetch_command_error",
          data: { name: e && e.name, message: e && String(e.message || e) },
          timestamp: Date.now(),
          hypothesisId: "E",
          runId: "pre-fix",
        }),
      }).catch(function () {});
      // #endregion
      if (e && e.name === "AbortError") return;
      el.result.textContent = "Could not reach the server. Start app.py and refresh.";
      el.result.classList.add("err");
      speakResponse("Server connection failed.");
    }
  }

  function setupSpeech() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setMicBadge("Speech API unavailable — use text box", "badge-warn");
      el.btnListen.disabled = true;
      el.btnLabel.textContent = "Use typing";
      return;
    }

    recognition = new SR();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = function () {
      listening = true;
      el.btnListen.classList.add("listening");
      el.btnListen.setAttribute("aria-pressed", "true");
      setMicBadge("Listening for 'New'…", "badge-listening");
      el.btnLabel.textContent = "Listening for 'New'…";
    };

    recognition.onend = function () {
      listening = false;
      el.btnListen.classList.remove("listening");
      el.btnListen.setAttribute("aria-pressed", "false");
      // Always restart continuous listening
      setTimeout(() => {
        try {
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.start();
        } catch {
          /* already starting */
        }
      }, 100);
    };

    recognition.onerror = function (ev) {
      if (ev.error === "not-allowed") {
        setMicBadge("Mic blocked — allow in browser", "badge-err");
        el.result.textContent = "Microphone permission denied.";
        el.result.classList.add("err");
      } else if (ev.error === "no-speech") {
        setMicBadge("No speech detected", "badge-warn");
      }
    };

    recognition.onresult = function (event) {
      const last = event.results[event.results.length - 1];
      const text = last[0].transcript.trim().toLowerCase();
      
      console.log('Speech detected:', text, 'isFinal:', last.isFinal); // Debug log
      
      // Always listening for "New" activation
      if (text) {
        if ((text.includes("new") || text === "new" || text.endsWith("new"))) {
          console.log('New activation detected!'); // Debug log
          
          // Only respond if this is final or if we haven't detected yet
          if (last.isFinal || !activationWordDetected) {
            activationWordDetected = true;
            setMicBadge("New detected! Listening for command…", "badge-ok");
            el.btnLabel.textContent = "Speak your command";
            speakResponse("Yes, I'm listening!");
            
            // Switch to command mode temporarily
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.stop();
            
            // Start command listening after a short delay
            setTimeout(() => {
              try {
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.start();
              } catch {
                /* */
              }
            }, 500);
          }
        } else if (activationWordDetected) {
          if (last.isFinal) {
            console.log('Processing command:', text); // Debug log
            sendCommand(last[0].transcript.trim());
            
            // Return to continuous listening after command
            activationWordDetected = false;
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.stop();
            setTimeout(() => {
              try {
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.start();
              } catch {
                /* */
              }
            }, 1000);
          }
        }
      }
    };
  }

  function startListen() {
    if (!recognition) return;
    continuousListening = true;
    activationWordDetected = false;
    recognition.continuous = true;
    recognition.interimResults = true;
    try {
      recognition.start();
      setMicBadge("Listening for 'New'…", "badge-listening");
      el.btnLabel.textContent = "Listening for 'New'…";
      console.log('Continuous listening started'); // Debug log
    } catch (error) {
      console.log('Error starting continuous listening:', error); // Debug log
    }
  }

  function startContinuousListening() {
    // This is now the default behavior - just start listening
    startListen();
  }

  function stopContinuousListening() {
    if (!recognition) return;
    continuousListening = false;
    activationWordDetected = false;
    recognition.continuous = false;
    try {
      recognition.stop();
      setMicBadge("Microphone idle", "badge-idle");
      el.btnLabel.textContent = "Click to start listening";
    } catch {
      /* */
    }
  }

  function stopListen() {
    if (!recognition) return;
    try {
      recognition.stop();
    } catch {
      /* */
    }
  }

  el.btnListen.addEventListener("click", function () {
    if (el.btnListen.disabled) return;
    if (continuousListening) {
      stopContinuousListening();
    } else {
      startContinuousListening();
    }
  });

  el.btnListen.addEventListener("pointerleave", function () {
    if (listening) stopListen();
  });

  el.btnSend.addEventListener("click", function () {
    sendCommand(el.textCmd.value);
  });

  el.textCmd.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      sendCommand(el.textCmd.value);
    }
  });

  setupSpeech();
  checkHealth();
  
  // Auto-start continuous listening
  setTimeout(() => {
    startContinuousListening();
  }, 1000);
  
  // Load voices when available and ensure speech works
  if ('speechSynthesis' in window) {
    function loadVoices() {
      const voices = speechSynthesis.getVoices();
      console.log('Available voices:', voices.length);
      voices.forEach((voice, index) => {
        console.log(`${index}: ${voice.name} (${voice.lang})`);
      });
    }
    
    speechSynthesis.getVoices();
    speechSynthesis.onvoiceschanged = loadVoices;
    
    // Test speech synthesis on load
    setTimeout(() => {
      console.log('Testing speech synthesis...');
      const testUtterance = new SpeechSynthesisUtterance("Voice system ready");
      testUtterance.volume = 0.1; // Quiet test
      speechSynthesis.speak(testUtterance);
    }, 2000);
  }
  
  // Add keyboard shortcut for continuous listening
  document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.shiftKey && e.key === 'z') {
      e.preventDefault();
      if (continuousListening) {
        stopContinuousListening();
      } else {
        startContinuousListening();
      }
    }
  });
})();
