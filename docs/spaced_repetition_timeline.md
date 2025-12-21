# Spaced Repetition System - Implementation Timeline

## Overview

This timeline shows how our **multi-source ML-enhanced spaced repetition system** works, from day 1 (pure SM-2) through ML model training and deployment.

**Key Innovation:** We use **verified data sources** (quiz attempts, match quiz attempts) with higher confidence weights than self-reported flashcard reviews.

---

## Phase 1: Baseline System (Week 1)

### Days 1-30: User Studies with SM-2 Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│ DAYS 1-30: User Studies (0-100+ interactions)                   │
│                                                                  │
│  User reviews flashcards → SM-2 calculates next review          │
│  User takes quizzes      → Verified performance data            │
│  User plays match quiz   → Verified matching data               │
│                          ↓                                       │
│                    All interactions logged                       │
│                          ↓                                       │
│                 [UnifiedReviewLogger]                            │
│                          ↓                                       │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ review_events.jsonl (or Supabase)                     │       │
│  ├──────────────────────────────────────────────────────┤       │
│  │ {"interaction_type": "flashcard_review",              │       │
│  │  "confidence_weight": 0.3,  ← LOW (self-reported)    │       │
│  │  "was_correct": true, ...}                            │       │
│  │                                                        │       │
│  │ {"interaction_type": "quiz_attempt",                  │       │
│  │  "confidence_weight": 0.9,  ← HIGH (verified)        │       │
│  │  "was_correct": true, ...}                            │       │
│  │                                                        │       │
│  │ {"interaction_type": "match_attempt",                 │       │
│  │  "confidence_weight": 0.85, ← HIGH (verified)        │       │
│  │  "was_correct": false, ...}                           │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  Flashcard Review #1  ────→ [JSONL] (weight: 0.3)              │
│  Quiz Attempt #1      ────→ [JSONL] (weight: 0.9) ✓ Verified   │
│  Match Attempt #1     ────→ [JSONL] (weight: 0.85) ✓ Verified  │
│  Flashcard Review #2  ────→ [JSONL] (weight: 0.3)              │
│  Quiz Attempt #2      ────→ [JSONL] (weight: 0.9) ✓ Verified   │
│  ...                                                             │
│  Interaction #100     ────→ [JSONL] ✅ Threshold reached!       │
│                                                                  │
│  Verified Interactions: 40+ (quizzes + matches)                 │
│  Self-Reported: 60 (flashcard reviews)                          │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- System works immediately with SM-2 (no ML needed yet)
- All interaction types are logged with appropriate confidence weights
- Tag-based linking connects flashcards to quiz/match questions
- Verified data (quiz/match) gets 3x weight of self-reported data

---

## Phase 2: ML Training Trigger

```
┌─────────────────────────────────────────────────────────────────┐
│ TRIGGER: System detects 100+ total interactions                 │
│          (with at least 30 verified interactions)               │
│                                                                  │
│  Option A: Automatic (cronjob checks daily)                     │
│  Option B: Manual (admin runs training script)                  │
│  Option C: On-demand (user clicks "Train Personal Model")       │
│                                                                  │
│  Requirements:                                                   │
│  ✅ Total interactions >= 100                                    │
│  ✅ Verified interactions (quiz + match) >= 30                   │
│  ✅ At least 3 different topics/tags covered                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 3: Data Preparation (~30 seconds)

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: DATA PREPARATION (~30 seconds)                         │
│                                                                  │
│  1. Load review_events.jsonl (or Supabase)                      │
│     → 100 total interactions loaded                             │
│     → 40 verified (quiz + match)                                │
│     → 60 self-reported (flashcard reviews)                      │
│                                                                  │
│  2. Tag-based feature enrichment                                │
│     For each flashcard:                                         │
│       ┌──────────────────────────────────────────────┐          │
│       │ Flashcard: "What produces ATP?"              │          │
│       │ Tags: ["biology", "cell", "mitochondria"]    │          │
│       │                                               │          │
│       │ Find related quiz questions with same tags:  │          │
│       │   Quiz Q1 (biology, mitochondria): ✓ Correct│          │
│       │   Quiz Q2 (cell, mitochondria): ✓ Correct   │          │
│       │   Quiz Q3 (biology, cell): ✗ Incorrect      │          │
│       │                                               │          │
│       │ Calculate tag-based features:                │          │
│       │   - tag_quiz_accuracy: 66% (2/3 correct)     │          │
│       │   - tag_match_accuracy: 80% (from matches)   │          │
│       │   - tag_consistency: 0.14 (low variance)     │          │
│       └──────────────────────────────────────────────┘          │
│                                                                  │
│  3. Transform JSON → Numerical Features                         │
│     Before:                                                      │
│       {"was_correct": true, "response_time": 5.3,               │
│        "interaction_type": "quiz_attempt",                      │
│        "confidence_weight": 0.9,                                │
│        "tag_quiz_accuracy": 0.66, ...}                          │
│                                                                  │
│     After (feature vector):                                     │
│       tensor([1, 5.3, 3, 2.5, 0.66, 0.80, 0.14, 0.9, ...])     │
│       #      │   │   │   │     │     │     │     │              │
│       #      │   │   │   │     │     │     │     └─ confidence  │
│       #      │   │   │   │     │     │     └─ tag_consistency   │
│       #      │   │   │   │     │     └─ tag_match_accuracy      │
│       #      │   │   │   │     └─ tag_quiz_accuracy (VERIFIED)  │
│       #      │   │   │   └─ ease_factor                         │
│       #      │   │   └─ repetitions                             │
│       #      │   └─ response_time                               │
│       #      └─ was_correct (1=yes, 0=no)                       │
│                                                                  │
│  4. Weighted sampling for training                              │
│     Quiz attempt (weight 0.9):     Sampled 3x more often       │
│     Match attempt (weight 0.85):   Sampled 3x more often       │
│     Flashcard review (weight 0.3): Sampled at base rate        │
│                                                                  │
│     Effective training data:                                    │
│     → 40 verified × 3 = 120 weighted samples                    │
│     → 60 self-reported × 1 = 60 weighted samples                │
│     → Total: 180 weighted training samples                      │
│                                                                  │
│  5. Train/Validation Split (80/20)                              │
│     → Train: 144 weighted samples                               │
│     → Validation: 36 weighted samples                           │
│                                                                │
│  6. Normalization (StandardScaler)                              │
│     response_time: 2-15s → 0.0-1.0                             │
│     ease_factor: 1.3-2.5 → 0.0-1.0                             │
│     tag_quiz_accuracy: 0-1 → already normalized                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Innovation:** Tag-based cross-source features enable the model to learn from quiz/match performance and apply that knowledge to flashcard retention predictions.

---

## Phase 4: Model Training (~2-5 minutes)

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: TRAINING (~2-5 minutes on GTX 1050)                    │
│                                                                  │
│  PyTorch Neural Network:                                         │
│  ┌────────────────────────────────────────────────────┐         │
│  │ Input Layer (13 features)                          │         │
│  │   ├─ Card features (ease_factor, repetitions, ...) │         │
│  │   ├─ Verified quiz features (tag_quiz_accuracy)    │         │
│  │   ├─ Verified match features (tag_match_accuracy)  │         │
│  │   └─ Confidence weight                             │         │
│  │         ↓                                           │         │
│  │ Hidden Layer 1 (64 neurons) + ReLU + Dropout       │         │
│  │         ↓                                           │         │
│  │ Hidden Layer 2 (32 neurons) + ReLU + Dropout       │         │
│  │         ↓                                           │         │
│  │ Hidden Layer 3 (16 neurons) + ReLU                 │         │
│  │         ↓                                           │         │
│  │ Output Layer (1 neuron) + Sigmoid                  │         │
│  │  → Retention Probability (0.0 to 1.0)              │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                  │
│  Training Progress:                                              │
│  ────────────────────────────────────────────────────           │
│  EPOCH 1/50:  Train Loss=0.523  Val Loss=0.548  Val Acc=62%    │
│               [██░░░░░░░░]                                      │
│                                                                  │
│  EPOCH 10/50: Train Loss=0.312  Val Loss=0.335  Val Acc=78%    │
│               [████░░░░░░] ← Model learning verified patterns   │
│                                                                  │
│  EPOCH 25/50: Train Loss=0.187  Val Loss=0.201  Val Acc=85%    │
│               [██████░░░░] ← High accuracy on verified data     │
│                                                                  │
│  EPOCH 35/50: Train Loss=0.142  Val Loss=0.198  Val Acc=86%    │
│               [███████░░░]                                      │
│               ⚠️  Early stopping triggered! (no improvement)    │
│                                                                  │
│  ✅ Training complete!                                           │
│     - Final validation accuracy: 86%                            │
│     - Verified data accuracy: 91% (quiz/match predictions)      │
│     - Self-reported accuracy: 78% (flashcard predictions)       │
│     - No overfitting detected (train/val gap: 3%)               │
│                                                                  │
│  Save model:                                                     │
│  → models/user_123_model_v1.pth (2.5 MB)                        │
│  → models/user_123_scaler.pkl (50 KB)                           │
│  → models/user_123_metadata.json (training stats)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 5: Deployment (Instant)

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: DEPLOYMENT (Instantaneous)                             │
│                                                                  │
│  1. API loads new model                                          │
│     model = load_model('user_123_model_v1.pth')                 │
│     scaler = load_scaler('user_123_scaler.pkl')                 │
│                                                                  │
│  2. Set ML confidence based on verified interactions            │
│     verified_count = 40 (quiz + match attempts)                 │
│     ml_confidence = min(0.8, (40 / 100) * 0.8) = 0.32          │
│     # Will gradually increase to 0.8 with more verified data    │
│                                                                  │
│  3. Activate "ML mode" for this user                            │
│     user.ml_model_active = True                                 │
│     user.ml_confidence = 0.32                                   │
│                                                                  │
│  4. Notify user:                                                │
│     "🎉 Your personal ML model is active!                       │
│      Trained on 40 verified quiz/match attempts.               │
│      Reviews are now personalized to your learning patterns."   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 6: Real-Time Predictions (<50ms)

```
┌─────────────────────────────────────────────────────────────────┐
│ USAGE: User reviews next flashcard (Real-time, <50ms)           │
│                                                                  │
│  User clicks "Medium" on flashcard about mitochondria           │
│         ↓                                                        │
│  Frontend → POST /api/review-card                               │
│         ↓                                                        │
│  Backend Processing:                                             │
│  ──────────────────────────────────────────────────────         │
│    1. Load model (already in RAM, <1ms)                         │
│                                                                  │
│    2. Extract features from flashcard + user history:           │
│       ┌─────────────────────────────────────────────┐           │
│       │ Card Features:                              │           │
│       │   - difficulty: medium (encoded as 1)       │           │
│       │   - tags: ["biology", "cell", "mitochondria"]          │
│       │   - ease_factor: 2.5                        │           │
│       │   - repetitions: 3                          │           │
│       │   - response_time: 5.3s                     │           │
│       │                                              │           │
│       │ Verified Cross-Source Features (NEW!):      │           │
│       │   - tag_quiz_accuracy: 0.85                 │           │
│       │     (User scored 85% on "biology" quizzes)  │           │
│       │   - tag_match_accuracy: 0.78                │           │
│       │     (User matched 78% of "cell" pairs)      │           │
│       │   - tag_consistency: 0.12                   │           │
│       │     (Low variance = reliable knowledge)     │           │
│       │                                              │           │
│       │ Context Features:                           │           │
│       │   - hour_of_day: 14 (2 PM)                  │           │
│       │   - days_since_last_review: 6               │           │
│       └─────────────────────────────────────────────┘           │
│                                                                  │
│    3. Normalize features (scaler, <1ms)                         │
│       [1, 0, 0, 1, 2.5, 3, 0.65, 0.85, 0.78, 0.12, 14, 6]      │
│                                                                  │
│    4. ML model prediction (<5ms):                               │
│       retention_prob = model.predict(features)                  │
│       retention_prob = 0.82  # 82% chance of remembering       │
│                                                                  │
│    5. SM-2 baseline calculation (<1ms):                         │
│       sm2_interval = calculate_sm2(ease_factor=2.5, response=3) │
│       sm2_interval = 7 days                                     │
│                                                                  │
│    6. Hybrid prediction (weighted ensemble):                    │
│       ml_confidence = 0.32  # Based on 40 verified interactions│
│       sm2_weight = 1 - 0.32 = 0.68                             │
│       ml_weight = 0.32                                          │
│                                                                  │
│       sm2_interval = 7 days                                     │
│       ml_interval = calculate_from_retention(0.82) = 6 days    │
│                                                                  │
│       final_interval = (0.68 × 7) + (0.32 × 6)                 │
│                      = 4.76 + 1.92                             │
│                      = 6.68 → 7 days                           │
│                                                                  │
│    7. Log this review (continues data collection!):             │
│       ┌──────────────────────────────────────────┐             │
│       │ {"interaction_type": "flashcard_review", │             │
│       │  "confidence_weight": 0.3,               │             │
│       │  "was_correct": true,                    │             │
│       │  "ml_prediction": 0.82,                  │             │
│       │  "sm2_prediction": 7,                    │             │
│       │  "final_interval": 7}                    │             │
│       └──────────────────────────────────────────┘             │
│         ↓                                                        │
│  Frontend ← {"next_review_date": "2025-12-26",                 │
│              "days_until": 7,                                   │
│              "ml_confidence": 0.32,                             │
│              "retention_probability": 0.82}                     │
│         ↓                                                        │
│  User sees:                                                      │
│  ┌──────────────────────────────────────────────────┐           │
│  │ 📅 Next review: 7 days (Dec 26)                  │           │
│  │ 🎯 Predicted retention: 82%                      │           │
│  │ 🤖 ML confidence: 32% (40 verified interactions) │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

**Key Point:** The hybrid approach ensures SM-2 dominates early (68% weight) and ML gradually takes over as more verified data is collected.

---

## Phase 7: Continuous Improvement

```
┌─────────────────────────────────────────────────────────────────┐
│ CONTINUOUS IMPROVEMENT                                           │
│                                                                  │
│  Every 50 new verified interactions (quiz + match):             │
│  ──────────────────────────────────────────────────             │
│    → Retrain model with updated data                            │
│    → Increase ML confidence:                                     │
│                                                                  │
│       Verified count: 40  → ml_confidence = 0.32 (32% ML)       │
│       Verified count: 90  → ml_confidence = 0.72 (72% ML)       │
│       Verified count: 125 → ml_confidence = 0.80 (80% ML, cap)  │
│                                                                  │
│    → Model becomes increasingly accurate                         │
│    → Learns new patterns from user's behavior                   │
│    → Adapts to changing study habits                            │
│                                                                  │
│  Benefits of verified data focus:                               │
│  ────────────────────────────────────────────                   │
│    ✅ More reliable training signal (objective truth)            │
│    ✅ Reduces impact of user self-reporting bias                 │
│    ✅ Cross-validates knowledge across interaction types         │
│    ✅ Enables topic-specific retention modeling                  │
│                                                                  │
│  Example progression:                                            │
│  ────────────────────────────────────────────                   │
│    Week 1:  Pure SM-2 (0 verified interactions)                 │
│    Week 3:  32% ML, 68% SM-2 (40 verified)                      │
│    Week 6:  64% ML, 36% SM-2 (80 verified)                      │
│    Week 10: 80% ML, 20% SM-2 (100+ verified) ← Optimal blend    │
│                                                                  │
│    SM-2 always provides 20% safety net (prevents ML errors)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary: Multi-Source Data Flow

```
┌────────────────────────────────────────────────────────────────┐
│                   USER LEARNING ACTIVITIES                      │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Flashcard    │  │ Quiz        │  │ Match Quiz          │   │
│  │ Review       │  │ Attempt     │  │ Attempt             │   │
│  │ (weight 0.3) │  │ (weight 0.9)│  │ (weight 0.85)       │   │
│  └──────┬───────┘  └──────┬──────┘  └──────┬──────────────┘   │
│         │                 │                 │                  │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           ↓                                     │
│              ┌────────────────────────┐                         │
│              │ UnifiedReviewLogger    │                         │
│              │ - Tags linking         │                         │
│              │ - Confidence weighting │                         │
│              │ - Timestamping         │                         │
│              └────────────┬───────────┘                         │
│                           ↓                                     │
│              ┌────────────────────────┐                         │
│              │ review_events.jsonl    │                         │
│              └────────────┬───────────┘                         │
│                           │                                     │
│       ┌───────────────────┼────────────────────┐               │
│       │                   │                    │               │
│       ↓                   ↓                    ↓               │
│  ┌─────────┐      ┌──────────────┐     ┌─────────────┐        │
│  │  SM-2   │      │   Feature    │     │  ML Model   │        │
│  │ Engine  │      │  Extraction  │     │  (PyTorch)  │        │
│  │(Always) │      │ (Tag-based)  │     │ (Week 5+)   │        │
│  └────┬────┘      └──────┬───────┘     └──────┬──────┘        │
│       │                  │                    │               │
│       └──────────────────┼────────────────────┘               │
│                          ↓                                     │
│              ┌───────────────────────┐                         │
│              │   Hybrid Predictor    │                         │
│              │ (Weighted Ensemble)   │                         │
│              │                       │                         │
│              │ prediction =          │                         │
│              │   (1-conf) × SM-2 +   │                         │
│              │   conf × ML           │                         │
│              └───────────┬───────────┘                         │
│                          ↓                                     │
│              ┌───────────────────────┐                         │
│              │ Optimal Review Date   │                         │
│              │ + Retention Estimate  │                         │
│              └───────────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Metrics & Thresholds

| Metric | Threshold | Purpose |
|--------|-----------|---------|
| **Total Interactions** | 100+ | Minimum data for reliable ML training |
| **Verified Interactions** | 30+ | Ensures objective training signal |
| **ML Confidence** | 0.0 → 0.8 | Gradual transition from SM-2 to ML |
| **Verified per ML Confidence** | 100 verified = 0.8 | Formula: `min(0.8, verified/100 × 0.8)` |
| **Retraining Frequency** | Every 50 verified | Keeps model up-to-date |
| **Early Stopping Patience** | 10 epochs | Prevents overfitting |
| **Max ML Weight** | 80% | SM-2 always provides 20% safety net |

---

## Advantages of Multi-Source Approach

### 1. **Objective Truth from Quizzes**
- Quiz answers are verifiable (correct/incorrect)
- No user bias ("I think I remember" → actual test)
- Higher confidence weight (0.9 vs 0.3)

### 2. **Cross-Validation via Matches**
- Tests recall in different format
- Confirms knowledge consistency
- Detects surface-level vs deep understanding

### 3. **Tag-Based Intelligence**
- ML learns topic-specific retention patterns
- User strong in "biology" → flashcards in that topic get different predictions
- Enables fine-grained personalization

### 4. **Reliability Scoring**
- `tag_consistency` feature detects when user performs differently across quiz/match/review
- Low consistency = uncertain knowledge → shorter intervals
- High consistency = reliable knowledge → longer intervals

### 5. **Progressive Enhancement**
- System works perfectly from day 1 (SM-2)
- ML confidence increases only with verified data
- Never relies 100% on ML (80% cap preserves SM-2 wisdom)

---

## Implementation Checklist

### Week 1: SM-2 + Multi-Source Logging
- [ ] Update `FlashCard` model with SM-2 fields
- [ ] Create `ReviewInteraction` model with `interaction_type` and `confidence_weight`
- [ ] Implement `UnifiedReviewLogger` class
- [ ] Add logging to flashcard review workflow
- [ ] Add logging to quiz completion (all questions)
- [ ] Add logging to match quiz completion
- [ ] Implement SM-2 algorithm in `core/spaced_repetition.py`
- [ ] Test with simulated user sessions

### Week 2-3: Tag-Based Linking
- [ ] Auto-generate tags for existing flashcards (Gemini)
- [ ] Auto-generate tags for quiz questions
- [ ] Auto-generate tags for match pairs
- [ ] Create tag coverage analytics
- [ ] Verify linking effectiveness (>80% coverage)

### Week 4: Feature Engineering
- [ ] Implement tag-based feature extraction
- [ ] Create `tag_quiz_accuracy` calculator
- [ ] Create `tag_match_accuracy` calculator
- [ ] Create `tag_consistency_score` calculator
- [ ] Build feature normalization pipeline

### Week 5: ML Model
- [ ] Implement PyTorch `RetentionPredictor` model
- [ ] Create weighted sampling function
- [ ] Implement training loop with early stopping
- [ ] Create hybrid prediction ensemble
- [ ] Test on validation set (target: >80% accuracy on verified data)

### Week 6: Deployment & Testing
- [ ] Model loading/caching in API
- [ ] Real-time prediction endpoint (<50ms)
- [ ] ML confidence calculation based on verified count
- [ ] User notification system
- [ ] A/B testing framework (SM-2 vs Hybrid)
- [ ] Monitoring dashboard (prediction accuracy, retention curves)

---

**Document Version:** 2.0 (Multi-Source Enhanced)
**Last Updated:** 2025-12-19
**Key Innovation:** Verified quiz/match data prioritized over self-reported reviews
