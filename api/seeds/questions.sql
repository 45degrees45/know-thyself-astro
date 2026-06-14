-- AstroWise Question Bank Seed Data
-- Run against the production DB after migrations:
--   psql $DATABASE_URL < api/seeds/questions.sql

-- know_thyself tab
INSERT INTO question_bank (tab, question, click_count, lagna_filter, active) VALUES
('know_thyself', 'What is my lagna and what does it reveal about my core nature?', 0, NULL, TRUE),
('know_thyself', 'Which planet is most dominant in my chart and why?', 0, NULL, TRUE),
('know_thyself', 'What does my Moon nakshatra say about my emotional nature?', 0, NULL, TRUE),
('know_thyself', 'What are the shadow traits I need to watch out for?', 0, NULL, TRUE),
('know_thyself', 'What is my spirit animal and what does it mean for me?', 0, NULL, TRUE),
('know_thyself', 'Which yogas do I have and how strong are they?', 0, NULL, TRUE),
('know_thyself', 'What is my greatest strength according to this chart?', 0, NULL, TRUE),
('know_thyself', 'How does my current dasha period shape my personality right now?', 0, NULL, TRUE),
('know_thyself', 'What part of myself am I still hiding or suppressing?', 0, NULL, TRUE),
('know_thyself', 'What is the lesson of my 12th house?', 0, NULL, TRUE);

-- career tab
INSERT INTO question_bank (tab, question, click_count, lagna_filter, active) VALUES
('career', 'What career fields best suit my chart?', 0, NULL, TRUE),
('career', 'What is my ideal work environment according to my placements?', 0, NULL, TRUE),
('career', 'When is the best window for a career breakthrough?', 0, NULL, TRUE),
('career', 'Which planets support my professional success?', 0, NULL, TRUE),
('career', 'Should I work independently or within a structure?', 0, NULL, TRUE),
('career', 'What does my 10th house reveal about my public reputation?', 0, NULL, TRUE),
('career', 'How does my current dasha affect my career trajectory?', 0, NULL, TRUE),
('career', 'What obstacles does my chart show in career growth and how to overcome them?', 0, NULL, TRUE),
('career', 'Am I in the right field for my chart?', 0, NULL, TRUE),
('career', 'What skills should I develop based on my planetary strengths?', 0, NULL, TRUE);

-- relationship tab
INSERT INTO question_bank (tab, question, click_count, lagna_filter, active) VALUES
('relationship', 'What does my 7th house say about my ideal partner?', 0, NULL, TRUE),
('relationship', 'When is a strong period for committed relationships or marriage?', 0, NULL, TRUE),
('relationship', 'What relationship patterns does my Venus placement create?', 0, NULL, TRUE),
('relationship', 'What am I most afraid of in relationships according to my chart?', 0, NULL, TRUE),
('relationship', 'How does my Moon sign affect how I give and receive love?', 0, NULL, TRUE),
('relationship', 'What does my chart say about compatibility with fire signs?', 0, NULL, TRUE),
('relationship', 'What is my attachment style based on my 4th house and Moon?', 0, NULL, TRUE),
('relationship', 'What challenges might I face in long-term partnerships?', 0, NULL, TRUE),
('relationship', 'Does my chart show a tendency to attract karmic relationships?', 0, NULL, TRUE),
('relationship', 'How does my Rahu or Ketu placement affect my relationships?', 0, NULL, TRUE);

-- spiritual tab
INSERT INTO question_bank (tab, question, click_count, lagna_filter, active) VALUES
('spiritual', 'What is my dharma or life purpose according to this chart?', 0, NULL, TRUE),
('spiritual', 'Which planet is my spiritual guide and how do I connect with it?', 0, NULL, TRUE),
('spiritual', 'What does my 12th house reveal about my spiritual path?', 0, NULL, TRUE),
('spiritual', 'What karmic patterns does my Rahu–Ketu axis reveal?', 0, NULL, TRUE),
('spiritual', 'What remedies suit my chart most — mantra, gemstone, or behavioral?', 0, NULL, TRUE),
('spiritual', 'What is the deeper meaning of my current dasha from a spiritual lens?', 0, NULL, TRUE),
('spiritual', 'Which nakshatra energies should I work with for inner growth?', 0, NULL, TRUE),
('spiritual', 'What past-life patterns might my Saturn placement be asking me to resolve?', 0, NULL, TRUE),
('spiritual', 'How can I use my spirit animal as a daily guide?', 0, NULL, TRUE),
('spiritual', 'What practices would most balance my dominant planetary energy?', 0, NULL, TRUE);

-- trending tab
INSERT INTO question_bank (tab, question, click_count, lagna_filter, active) VALUES
('trending', 'What does 2026 look like for me based on my dasha and transits?', 0, NULL, TRUE),
('trending', 'Is Saturn currently challenging or supporting my chart?', 0, NULL, TRUE),
('trending', 'How does the current Jupiter transit affect my lagna?', 0, NULL, TRUE),
('trending', 'What is the biggest opportunity in my chart for the next 12 months?', 0, NULL, TRUE),
('trending', 'When will my current difficult period ease?', 0, NULL, TRUE),
('trending', 'What does Rahu transiting my chart mean for my ambitions?', 0, NULL, TRUE),
('trending', 'Is this a good time to start something new or consolidate?', 0, NULL, TRUE),
('trending', 'What financial themes does my chart show for this year?', 0, NULL, TRUE),
('trending', 'How will the upcoming eclipse season affect my chart?', 0, NULL, TRUE),
('trending', 'What is the most important transit to watch in the next 6 months?', 0, NULL, TRUE);

-- weekly_questions seed
INSERT INTO weekly_questions (question, week_of, active) VALUES
('Where in your life are you still performing rather than truly being?', '2026-W25', TRUE),
('What fear disguises itself as a practical reason in your life?', '2026-W26', TRUE),
('What would you do differently if no one was watching?', '2026-W27', TRUE),
('Which relationship in your life mirrors something you have not accepted in yourself?', '2026-W28', TRUE);
