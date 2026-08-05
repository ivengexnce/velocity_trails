/**
 * ══════════════════════════════════════════════
 *  TECHCHASE 2K26 — FIREBASE CONFIG
 *  Replace the values below with your Firebase
 *  project credentials from:
 *  console.firebase.google.com → Project Settings
 * ══════════════════════════════════════════════
 */

const FIREBASE_CONFIG = {
  apiKey:            "YOUR_API_KEY",
  authDomain:        "YOUR_PROJECT_ID.firebaseapp.com",
  projectId:         "YOUR_PROJECT_ID",
  storageBucket:     "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId:             "YOUR_APP_ID"
};

/* ── Init ── */
if (!firebase.apps.length) {
  firebase.initializeApp(FIREBASE_CONFIG);
}
const db = firebase.firestore();
const AGENTS_COL = 'tc_agents'; // Firestore collection name

/* ═══════════════════════════════════════════
   SAVE — call this when a player registers
   Usage: await saveAgentToFirebase({ name, roll, dept, year, phone, score })
   Returns the new document ID or null on failure.
═══════════════════════════════════════════ */
async function saveAgentToFirebase(agentData) {
  try {
    const payload = {
      name:  agentData.name  || '',
      roll:  agentData.roll  || '',
      dept:  agentData.dept  || '',
      year:  agentData.year  || '',
      phone: agentData.phone || '',
      score: agentData.score || 0,
      ts:    agentData.ts    || Date.now(),
      createdAt: firebase.firestore.FieldValue.serverTimestamp()
    };
    const ref = await db.collection(AGENTS_COL).add(payload);

    /* Also mirror to localStorage as offline cache */
    try {
      const cached = JSON.parse(localStorage.getItem('tc_agents') || '[]');
      cached.push({ ...payload, _id: ref.id });
      localStorage.setItem('tc_agents', JSON.stringify(cached));
    } catch (_) {}

    return ref.id;
  } catch (err) {
    console.error('[TechChase] saveAgent failed:', err);
    return null;
  }
}

/* ═══════════════════════════════════════════
   GET ALL — one-time fetch, sorted by score desc
   Returns array of agent objects.
═══════════════════════════════════════════ */
async function getAgentsFromFirebase() {
  try {
    const snap = await db.collection(AGENTS_COL)
      .orderBy('score', 'desc')
      .get();
    return snap.docs.map(d => ({ _id: d.id, ...d.data() }));
  } catch (err) {
    console.error('[TechChase] getAgents failed:', err);
    /* Fallback to localStorage cache */
    try { return JSON.parse(localStorage.getItem('tc_agents') || '[]'); }
    catch (_) { return []; }
  }
}

/* ═══════════════════════════════════════════
   REAL-TIME LISTENER — fires whenever data changes
   Usage: const unsub = onAgentsUpdate(agents => { ... });
          unsub(); // to stop listening
═══════════════════════════════════════════ */
function onAgentsUpdate(callback) {
  return db.collection(AGENTS_COL)
    .orderBy('score', 'desc')
    .onSnapshot(
      snap => {
        const agents = snap.docs.map(d => ({ _id: d.id, ...d.data() }));
        callback(agents);
      },
      err => {
        console.error('[TechChase] onAgentsUpdate error:', err);
        /* Fallback to cached data on error */
        try { callback(JSON.parse(localStorage.getItem('tc_agents') || '[]')); }
        catch (_) { callback([]); }
      }
    );
}

/* ═══════════════════════════════════════════
   CLEAR ALL — deletes every document in batches
   (Firestore max batch = 500)
═══════════════════════════════════════════ */
async function clearAgentsFromFirebase() {
  try {
    const snap = await db.collection(AGENTS_COL).get();
    const batchSize = 400;
    let i = 0;
    while (i < snap.docs.length) {
      const batch = db.batch();
      snap.docs.slice(i, i + batchSize).forEach(d => batch.delete(d.ref));
      await batch.commit();
      i += batchSize;
    }
    localStorage.removeItem('tc_agents');
    localStorage.removeItem('tc_player');
    return true;
  } catch (err) {
    console.error('[TechChase] clearAgents failed:', err);
    return false;
  }
}

/* ═══════════════════════════════════════════
   UPDATE SCORE — update score for a specific agent by doc ID
   Usage: await updateAgentScore(docId, 1500)
═══════════════════════════════════════════ */
async function updateAgentScore(docId, score) {
  try {
    await db.collection(AGENTS_COL).doc(docId).update({ score });
    return true;
  } catch (err) {
    console.error('[TechChase] updateScore failed:', err);
    return false;
  }
}
