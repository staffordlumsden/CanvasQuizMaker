#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import html
import re
import shutil
import subprocess
import tempfile
from email import policy
from email.parser import BytesParser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from text2qti.config import Config
from text2qti.err import Text2qtiError
from text2qti.qti import QTI
from text2qti.quiz import GroupStart, Question, Quiz, TextRegion


REPO_ROOT = Path(__file__).resolve().parent
VENV_TEXT2QTI = REPO_ROOT / ".venv" / "bin" / "text2qti"


def _page(title: str, body_html: str) -> bytes:
    doc = f"""<!DOCTYPE html>
<html lang=\"en-AU\">
<head>
  <meta charset=\"utf-8\">
  <title>{html.escape(title)}</title>
  <style>
    input, textarea, select {{
      font-family: Menlo, Consolas, monospace;
      box-sizing: border-box;
      max-width: 100%;
    }}
  </style>
</head>
<body style=\"font-family: Montserrat, sans-serif; background-color: #f7f7f7; margin: 0; padding: 20px;\">
<center>
  <h1 style=\"margin-bottom: 8px;\">Canvas Quiz Builder</h1>
  <p style=\"margin-top: 0; margin-bottom: 16px;\"><b>v. 1.0 (February 2026) ©2026 Stafford Lumsden</b></p>
</center>
<div style=\"max-width: 980px; margin: 0 auto;\">{body_html}</div>
</body>
</html>"""
    return doc.encode("utf-8")


def _home_body() -> str:
    return """
<div style=\"padding: 14px; border: 1px solid #d1d1d1; border-radius: 15px; margin-bottom: 20px; background-color: #ffffff;\">
  <h2 style=\"margin-top: 0;\">Instructions</h2>
  <p style=\"margin: 0 0 8px 0;\">Build your quiz below using the <em>Guided Quiz Builder</em>.</p>
  <p style=\"margin: 0 0 6px 0;\">a. Give your quiz a filename.</p>
  <p style=\"margin: 0 0 6px 0;\">b. Add a quiz title and brief description as you want them to appear in Canvas.</p>
  <p style=\"margin: 0 0 6px 0;\">c. For each question, select the question type (Multiple Choice, Multiple Answer [e.g., \"choose all that apply\"], Short Answer, Numerical, Essay, or File Upload).</p>
  <p style=\"margin: 0 0 6px 0;\">d. Give a point value for the question.</p>
  <p style=\"margin: 0 0 6px 0;\">e. For each question provide overall feedback, feedback to correct answers and process-level feedback to incorrect answers (see below).</p>
  <p style=\"margin: 0;\">f. A live preview of your quiz will appear below the questions. When you are done click <b>Validate Builder Format</b> to check the formatting of your questions is correct then <b>Convert Builder to QTi</b> to save your quiz in a format that can be uploaded to Canvas.</p>
</div>

<div class=\"ic-Alert ic-Alert--warning\" role=\"alert\" style=\"background-color: #f4ede6; border: 2px solid #964100; color: #964100; border-radius: 8px; display: flex; align-items: flex-start; padding: 16px; font-family: Montserrat, sans-serif; margin: 20px 0;\">
    <div class=\"ic-Alert__icon\" style=\"margin-right: 16px; flex-shrink: 0;\"><svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z\"></path><line x1=\"12\" y1=\"9\" x2=\"12\" y2=\"13\"></line><line x1=\"12\" y1=\"17\" x2=\"12.01\" y2=\"17\"></line></svg></div>
    <div class=\"ic-Alert__content\">
        <h5 style=\"font-weight: 700; font-size: 1.125rem; margin-bottom: 8px; color: #964100; margin-top: 0;\">Multiple Choice Questions Information</h5>
        <p style=\"margin: 0 0 8px 0; color: #964100;\">a. Provide students with <em>distractors</em> (the wrong answers) that are plausible and require them to <b>discriminate</b> between the options they see.</p>
        <p style=\"margin: 0 0 8px 0; color: #964100;\">b. Avoid \"all of the above\" as this prevents decisions employing critical thinking and discrimination.</p>
        <p style=\"margin: 0; color: #964100;\">c. Add process-level feedback for both distractors and the correct answer.</p>
    </div>
</div>
<div style=\"display: flex; flex-direction: column; gap: 20px; margin-bottom: 20px;\">
  <div style=\"padding: 15px; border: 1px solid #d1d1d1; border-radius: 15px; background-color: #ffffff; min-width: 320px;\">
    <h2>Guided Quiz Builder</h2>
    <form id=\"builder-form\" action=\"/upload\" method=\"post\" enctype=\"multipart/form-data\">
      <input type=\"hidden\" id=\"builder-pasted-text\" name=\"pasted_text\" value=\"\">
      <p><label style=\"display:block; margin-top: 10px;\">Filename (without extension)</label>
      <input type=\"text\" id=\"builder-base-name\" name=\"base_name\" value=\"quiz-builder\" style=\"padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;\" required></p>
      <p><label style=\"display:block; margin-top: 10px;\">Quiz title</label>
      <input type=\"text\" id=\"builder-quiz-title\" value=\"\" style=\"padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;\" placeholder=\"e.g. Week 3 Quiz\"></p>
      <p><label style=\"display:block; margin-top: 10px;\">Quiz description</label>
      <textarea id=\"builder-quiz-description\" rows=\"3\" style=\"padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;\" placeholder=\"Brief description\"></textarea></p>
      <div id=\"builder-questions\" style=\"display:flex; flex-direction:column; gap:12px;\"></div>
      <p style=\"margin-top: 10px;\"><button type=\"button\" id=\"builder-add-question\" style=\"display:inline-block;text-decoration:none;text-align:center;padding:10px 12px;border-radius:10px;background-color:#ffffff;color:#1450A0;border:1px solid #1450A0;font-weight:700;\">Add Question</button></p>
      <div id=\"builder-issues\" style=\"display:none; margin-top: 12px; padding: 10px 12px; border-radius: 10px; background: #fff4e5; border: 1px solid #ffd28a; color: #7a4d00;\"></div>
      <p><label style=\"display:block; margin-top: 10px;\">Generated Text2QTI preview</label>
      <textarea id=\"builder-preview\" rows=\"10\" style=\"padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;\" readonly></textarea></p>
      <div id=\"builder-progress\" style=\"display:none; margin-top: 12px; padding: 10px 12px; border-radius: 10px; background: #f0f5ff; border: 1px solid #c7d6f7; color: #1a3d66; font-weight: 600;\">
        Processing builder content…
      </div>
      <p style=\"display:flex; gap: 10px; flex-wrap: wrap;\">
        <button type=\"submit\" data-working-text=\"Converting…\" style=\"display:inline-block;text-decoration:none;text-align:center;padding:10px 12px;border-radius:10px;background-color:#1450A0;color:#fff;border:1px solid #1450A0;font-weight:700;\">Convert Builder to QTi</button>
        <button type=\"submit\" formaction=\"/validate\" data-working-text=\"Validating…\" style=\"display:inline-block;text-decoration:none;text-align:center;padding:10px 12px;border-radius:10px;background-color:#0f766e;color:#fff;border:1px solid #0f766e;font-weight:700;\">Validate Builder Format</button>
      </p>
    </form>
  </div>

  <div style=\"padding: 15px; border: 1px solid #d1d1d1; border-radius: 15px; background-color: #ffffff; min-width: 320px;\">
    <h2>Paste & Convert</h2>
    <div style=\"padding: 10px; border: 1px solid #d1d1d1; border-radius: 10px; margin-bottom: 12px; background-color: #fafafa;\">
      If you have already created a QTi formatted quiz from a template etc. paste the content here and click <b>Validate Format</b> &gt; <b>Convert to QTi</b>.
    </div>
    <form id=\"paste-form\" action=\"/upload\" method=\"post\" enctype=\"multipart/form-data\">
      <p><textarea name=\"pasted_text\" rows=\"12\" style=\"padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;\" placeholder=\"Paste your Text2QTI content here...\" required></textarea></p>
      <p><label style=\"display:block; margin-top: 10px;\">Filename (without extension)</label>
      <input type=\"text\" name=\"base_name\" value=\"quiz\" style=\"padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;\" required></p>
      <div id=\"paste-progress\" style=\"display:none; margin-top: 12px; padding: 10px 12px; border-radius: 10px; background: #f0f5ff; border: 1px solid #c7d6f7; color: #1a3d66; font-weight: 600;\">
        Processing…
      </div>
      <p style=\"display:flex; gap: 10px; flex-wrap: wrap;\">
        <button type=\"submit\" data-working-text=\"Converting…\" style=\"display:inline-block;text-decoration:none;text-align:center;padding:10px 12px;border-radius:10px;background-color:#1450A0;color:#fff;border:1px solid #1450A0;font-weight:700;\">Convert to QTi</button>
        <button type=\"submit\" formaction=\"/validate\" data-working-text=\"Validating…\" style=\"display:inline-block;text-decoration:none;text-align:center;padding:10px 12px;border-radius:10px;background-color:#0f766e;color:#fff;border:1px solid #0f766e;font-weight:700;\">Validate Format</button>
      </p>
    </form>
  </div>
</div>

<div class=\"ic-Alert\" role=\"alert\" style=\"background-color: #e8eef6; border: 2px solid #1450A0; color: #1450A0; border-radius: 8px; display: flex; align-items: flex-start; padding: 16px; font-family: Montserrat, sans-serif;\">
  <div class=\"ic-Alert__icon\" style=\"margin-right: 16px; flex-shrink: 0;\"><svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"12\" cy=\"12\" r=\"10\"></circle><line x1=\"12\" y1=\"16\" x2=\"12\" y2=\"12\"></line><line x1=\"12\" y1=\"8\" x2=\"12.01\" y2=\"8\"></line></svg></div>
  <div class=\"ic-Alert__content\">
    <h5 style=\"font-weight: 700; font-size: 1.125rem; margin-bottom: 8px; color: #1450A0; margin-top: 0;\">Information</h5>
    <p style=\"margin: 0; color: #1450A0;\">This runs locally on your machine at http://localhost:8001.</p>
  </div>
</div>

<script>
(() => {
  const alphabet = "abcdefghijklmnopqrstuvwxyz";

  const pasteForm = document.getElementById("paste-form");
  const pasteProgress = document.getElementById("paste-progress");
  const pasteSubmitButtons = Array.from(pasteForm.querySelectorAll("button[type='submit']"));

  const builderForm = document.getElementById("builder-form");
  const builderQuestions = document.getElementById("builder-questions");
  const builderAddQuestion = document.getElementById("builder-add-question");
  const builderIssues = document.getElementById("builder-issues");
  const builderPreview = document.getElementById("builder-preview");
  const builderPastedText = document.getElementById("builder-pasted-text");
  const builderProgress = document.getElementById("builder-progress");
  const builderSubmitButtons = Array.from(builderForm.querySelectorAll("button[type='submit']"));

  let questionCounter = 0;

  pasteForm.addEventListener("submit", (event) => {
    pasteProgress.style.display = "block";
    for (const button of pasteSubmitButtons) {
      button.disabled = true;
    }
    if (event.submitter) {
      event.submitter.textContent = event.submitter.dataset.workingText || "Working…";
    }
  });

  const createChoiceRow = (correctChecked = false, choiceText = "", feedbackText = "") => {
    const rowWrap = document.createElement("div");
    rowWrap.className = "qb-choice-row";
    rowWrap.style.border = "1px solid #e3e3e3";
    rowWrap.style.borderRadius = "8px";
    rowWrap.style.padding = "8px";
    rowWrap.style.marginBottom = "8px";
    rowWrap.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; gap:8px;">
        <label style="display:flex; align-items:center; gap:4px; white-space:nowrap;">
          <input type="checkbox" class="qb-choice-correct" ${correctChecked ? "checked" : ""}> Correct
        </label>
        <button type="button" class="qb-remove-choice" style="padding:8px 10px; border-radius:8px; border:1px solid #bbb; background:#fff;">Remove</button>
      </div>
      <input type="text" class="qb-choice-text" value="${choiceText}" placeholder="Choice text" style="padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%; margin-bottom: 8px;">
      <input type="text" class="qb-choice-feedback" value="${feedbackText}" placeholder="Optional feedback for this choice" style="padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
    `;
    return rowWrap;
  };

  const createShortAnswerRow = (answerText = "") => {
    const rowWrap = document.createElement("div");
    rowWrap.className = "qb-shortans-row";
    rowWrap.style.display = "grid";
    rowWrap.style.gridTemplateColumns = "1fr auto";
    rowWrap.style.gap = "8px";
    rowWrap.style.marginBottom = "8px";
    rowWrap.innerHTML = `
      <input type="text" class="qb-shortans-text" value="${answerText}" placeholder="Accepted answer text" style="padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
      <button type="button" class="qb-remove-shortans" style="padding:8px 10px; border-radius:8px; border:1px solid #bbb; background:#fff;">Remove</button>
    `;
    return rowWrap;
  };

  const toggleTypeBlocks = (card) => {
    const type = card.querySelector(".qb-question-type").value;
    const choiceBlock = card.querySelector(".qb-choice-block");
    const shortansBlock = card.querySelector(".qb-shortans-block");
    const numericalBlock = card.querySelector(".qb-numerical-block");
    const essayNote = card.querySelector(".qb-essay-note");
    const uploadNote = card.querySelector(".qb-upload-note");

    choiceBlock.style.display = (type === "multiple_choice" || type === "multiple_answers") ? "block" : "none";
    shortansBlock.style.display = type === "short_answer" ? "block" : "none";
    numericalBlock.style.display = type === "numerical" ? "block" : "none";
    essayNote.style.display = type === "essay" ? "block" : "none";
    uploadNote.style.display = type === "file_upload" ? "block" : "none";
  };

  const reindexQuestions = () => {
    const cards = Array.from(builderQuestions.querySelectorAll(".qb-question-card"));
    cards.forEach((card, index) => {
      const label = card.querySelector(".qb-question-number");
      label.textContent = `Question ${index + 1}`;
    });
  };

  const addQuestionCard = () => {
    questionCounter += 1;
    const card = document.createElement("div");
    card.className = "qb-question-card";
    card.dataset.qid = String(questionCounter);
    card.style.border = "1px solid #d1d1d1";
    card.style.borderRadius = "12px";
    card.style.padding = "12px";
    card.style.background = "#fafafa";
    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:8px; flex-wrap:wrap;">
        <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
          <strong class="qb-question-number">Question</strong>
          <label style="display:flex; align-items:center; gap:6px;">
            <span>Type</span>
            <select class="qb-question-type" style="padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 260px;">
              <option value="multiple_choice">Multiple Choice</option>
              <option value="multiple_answers">Multiple Answer (choose all that apply)</option>
              <option value="short_answer">Short Answer</option>
              <option value="numerical">Numerical</option>
              <option value="essay">Essay</option>
              <option value="file_upload">File Upload</option>
            </select>
          </label>
        </div>
        <button type="button" class="qb-remove-question" style="padding:8px 10px; border-radius:8px; border:1px solid #bbb; background:#fff;">Remove Question</button>
      </div>
      <div style="display:grid; grid-template-columns: minmax(0, 1fr) 140px; gap:8px;">
        <input type="text" class="qb-question-title" placeholder="Optional question title" style="padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%; min-width: 0;">
        <label style="display:flex; flex-direction:column; gap:4px;">
          <span>Points</span>
          <input type="text" class="qb-question-points" value="1" style="padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
        </label>
      </div>
      <p style="margin-top:8px; margin-bottom:8px;">
        <textarea class="qb-question-stem" rows="3" placeholder="Question text" style="padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%; min-width: 0;"></textarea>
      </p>
      <div class="qb-choice-block" style="display:block; margin-top:8px;">
        <div class="qb-choices"></div>
        <button type="button" class="qb-add-choice" style="padding:8px 10px; border-radius:8px; border:1px solid #1450A0; background:#fff; color:#1450A0; font-weight:600;">Add Choice</button>
      </div>
      <div class="qb-shortans-block" style="display:none; margin-top:8px;">
        <div class="qb-shortans"></div>
        <button type="button" class="qb-add-shortans" style="padding:8px 10px; border-radius:8px; border:1px solid #1450A0; background:#fff; color:#1450A0; font-weight:600;">Add Accepted Answer</button>
      </div>
      <div class="qb-numerical-block" style="display:none; margin-top:8px;">
        <input type="text" class="qb-numerical-value" placeholder='e.g. 3 or [2.9, 3.1] or 3 +- 0.1' style="padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
      </div>
      <div class="qb-essay-note" style="display:none; margin-top:8px; color:#444;">Essay response marker (____) will be generated automatically.</div>
      <div class="qb-upload-note" style="display:none; margin-top:8px; color:#444;">File upload marker (^^^^) will be generated automatically.</div>
      <div style="margin-top:10px; display:grid; grid-template-columns:1fr; gap:8px;">
        <input type="text" class="qb-feedback-general" placeholder="Overall feedback (...)" style="padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
        <input type="text" class="qb-feedback-correct" placeholder="Feedback to correct answers (+)" style="padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
        <input type="text" class="qb-feedback-incorrect" placeholder="Process-level feedback to incorrect answers (-)" style="padding: 8px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
      </div>
    `;
    builderQuestions.appendChild(card);
    const choices = card.querySelector(".qb-choices");
    choices.appendChild(createChoiceRow(true));
    choices.appendChild(createChoiceRow(false));
    toggleTypeBlocks(card);
    reindexQuestions();
  };

  const parsePointsValue = (raw) => {
    const trimmed = raw.trim();
    if (!trimmed) {
      return { valid: true, value: "1" };
    }
    const num = Number(trimmed);
    if (!Number.isFinite(num) || num <= 0) {
      return { valid: false, value: trimmed };
    }
    const rounded = Math.round(num);
    const isHalf = Math.abs(num - rounded) === 0.5;
    const isInt = Number.isInteger(num);
    if (!isInt && !isHalf) {
      return { valid: false, value: trimmed };
    }
    return { valid: true, value: isInt ? String(rounded) : String(num) };
  };

  const collectBuilderModel = () => {
    const issues = [];
    const model = {
      baseName: document.getElementById("builder-base-name").value.trim() || "quiz-builder",
      quizTitle: document.getElementById("builder-quiz-title").value.trim(),
      quizDescription: document.getElementById("builder-quiz-description").value.trim(),
      questions: [],
    };

    const cards = Array.from(builderQuestions.querySelectorAll(".qb-question-card"));
    if (cards.length === 0) {
      issues.push("Add at least one question.");
    }

    cards.forEach((card, index) => {
      const qn = index + 1;
      const stem = card.querySelector(".qb-question-stem").value.trim();
      const type = card.querySelector(".qb-question-type").value;
      const title = card.querySelector(".qb-question-title").value.trim();
      const pointsRaw = card.querySelector(".qb-question-points").value;
      const points = parsePointsValue(pointsRaw);
      const feedbackGeneral = card.querySelector(".qb-feedback-general").value.trim();
      const feedbackCorrect = card.querySelector(".qb-feedback-correct").value.trim();
      const feedbackIncorrect = card.querySelector(".qb-feedback-incorrect").value.trim();

      if (!stem) {
        issues.push(`Question ${qn}: question text is required.`);
      }
      if (!points.valid) {
        issues.push(`Question ${qn}: points must be a positive integer or half-integer.`);
      }

      const question = {
        type,
        title,
        points: points.value,
        stem,
        feedbackGeneral,
        feedbackCorrect,
        feedbackIncorrect,
        choices: [],
        answers: [],
        numerical: "",
      };

      if (type === "multiple_choice" || type === "multiple_answers") {
        const choiceRows = Array.from(card.querySelectorAll(".qb-choice-row"));
        choiceRows.forEach((row) => {
          const text = row.querySelector(".qb-choice-text").value.trim();
          const correct = row.querySelector(".qb-choice-correct").checked;
          const feedback = row.querySelector(".qb-choice-feedback").value.trim();
          if (text) {
            question.choices.push({ text, correct, feedback });
          }
        });
        if (question.choices.length < 2) {
          issues.push(`Question ${qn}: provide at least two choices.`);
        }
        if (question.choices.length > alphabet.length) {
          issues.push(`Question ${qn}: maximum ${alphabet.length} choices are supported.`);
        }
        const correctCount = question.choices.filter((c) => c.correct).length;
        if (type === "multiple_choice" && correctCount !== 1) {
          issues.push(`Question ${qn}: multiple choice requires exactly one correct choice.`);
        }
        if (type === "multiple_answers" && correctCount < 1) {
          issues.push(`Question ${qn}: multiple answers requires at least one correct choice.`);
        }
      } else if (type === "short_answer") {
        const answerRows = Array.from(card.querySelectorAll(".qb-shortans-row"));
        answerRows.forEach((row) => {
          const text = row.querySelector(".qb-shortans-text").value.trim();
          if (text) {
            question.answers.push(text);
          }
        });
        if (question.answers.length < 1) {
          issues.push(`Question ${qn}: provide at least one accepted short answer.`);
        }
      } else if (type === "numerical") {
        const num = card.querySelector(".qb-numerical-value").value.trim();
        question.numerical = num;
        if (!num) {
          issues.push(`Question ${qn}: numerical response is required.`);
        }
      }

      model.questions.push(question);
    });

    return { model, issues };
  };

  const modelToText2Qti = (model) => {
    const lines = [];
    if (model.quizTitle) {
      lines.push(`Quiz title: ${model.quizTitle}`);
    }
    if (model.quizDescription) {
      lines.push(`Quiz description: ${model.quizDescription}`);
    }
    if (lines.length > 0) {
      lines.push("");
    }

    model.questions.forEach((q, i) => {
      if (q.title) {
        lines.push(`Title: ${q.title}`);
      }
      if (q.points) {
        lines.push(`Points: ${q.points}`);
      }
      lines.push(`${i + 1}.  ${q.stem}`);
      if (q.feedbackGeneral) {
        lines.push(`... ${q.feedbackGeneral}`);
      }
      if (q.feedbackCorrect) {
        lines.push(`+ ${q.feedbackCorrect}`);
      }
      if (q.feedbackIncorrect) {
        lines.push(`- ${q.feedbackIncorrect}`);
      }

      if (q.type === "multiple_choice") {
        q.choices.forEach((choice, idx) => {
          const letter = alphabet[idx];
          const marker = choice.correct ? `*${letter})  ` : `${letter})  `;
          lines.push(`${marker}${choice.text}`);
          if (choice.feedback) {
            lines.push(`... ${choice.feedback}`);
          }
        });
      } else if (q.type === "multiple_answers") {
        q.choices.forEach((choice) => {
          const marker = choice.correct ? "[*] " : "[ ] ";
          lines.push(`${marker}${choice.text}`);
          if (choice.feedback) {
            lines.push(`... ${choice.feedback}`);
          }
        });
      } else if (q.type === "short_answer") {
        q.answers.forEach((ans) => {
          lines.push(`* ${ans}`);
        });
      } else if (q.type === "numerical") {
        lines.push(`= ${q.numerical}`);
      } else if (q.type === "essay") {
        lines.push("____");
      } else if (q.type === "file_upload") {
        lines.push("^^^^");
      }
      lines.push("");
    });

    while (lines.length > 0 && lines[lines.length - 1] === "") {
      lines.pop();
    }
    return lines.join("\\n");
  };

  const renderBuilderPreview = () => {
    const { model, issues } = collectBuilderModel();
    const previewText = modelToText2Qti(model);
    builderPreview.value = previewText;
    if (issues.length > 0) {
      builderIssues.style.display = "block";
      builderIssues.innerHTML = `<b>Builder checks:</b><br>${issues.map((x) => `- ${x}`).join("<br>")}`;
    } else {
      builderIssues.style.display = "none";
      builderIssues.textContent = "";
    }
    return { issues, previewText };
  };

  builderQuestions.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    const card = target.closest(".qb-question-card");
    if (!card) {
      return;
    }
    if (target.classList.contains("qb-remove-question")) {
      card.remove();
      reindexQuestions();
      renderBuilderPreview();
      return;
    }
    if (target.classList.contains("qb-add-choice")) {
      card.querySelector(".qb-choices").appendChild(createChoiceRow(false));
      renderBuilderPreview();
      return;
    }
    if (target.classList.contains("qb-remove-choice")) {
      const rowNode = target.closest(".qb-choice-row");
      if (rowNode) {
        rowNode.remove();
        renderBuilderPreview();
      }
      return;
    }
    if (target.classList.contains("qb-add-shortans")) {
      card.querySelector(".qb-shortans").appendChild(createShortAnswerRow());
      renderBuilderPreview();
      return;
    }
    if (target.classList.contains("qb-remove-shortans")) {
      const rowNode = target.closest(".qb-shortans-row");
      if (rowNode) {
        rowNode.remove();
        renderBuilderPreview();
      }
    }
  });

  builderQuestions.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    const card = target.closest(".qb-question-card");
    if (!card) {
      return;
    }
    if (target.classList.contains("qb-question-type")) {
      toggleTypeBlocks(card);
    }
    renderBuilderPreview();
  });

  builderQuestions.addEventListener("input", () => {
    renderBuilderPreview();
  });

  builderForm.addEventListener("input", () => {
    renderBuilderPreview();
  });

  builderAddQuestion.addEventListener("click", () => {
    addQuestionCard();
    renderBuilderPreview();
  });

  builderForm.addEventListener("submit", (event) => {
    const { issues, previewText } = renderBuilderPreview();
    if (issues.length > 0) {
      event.preventDefault();
      return;
    }
    builderPastedText.value = previewText;
    builderProgress.style.display = "block";
    for (const button of builderSubmitButtons) {
      button.disabled = true;
    }
    if (event.submitter) {
      event.submitter.textContent = event.submitter.dataset.workingText || "Working…";
    }
  });

  addQuestionCard();
  renderBuilderPreview();
})();
</script>
"""


def _result_body(
    title: str,
    message: str,
    is_error: bool = False,
    allow_html: bool = False,
    actions_html: str = "",
) -> str:
    safe_msg = message if allow_html else html.escape(message)
    if is_error:
        alert = f"""
<div class=\"ic-Alert ic-Alert--danger\" role=\"alert\" style=\"background-color: #f9e8e8; border: 2px solid #a11c1c; color: #a11c1c; border-radius: 8px; display: flex; align-items: flex-start; padding: 16px; font-family: Montserrat, sans-serif;\">
  <div class=\"ic-Alert__icon\" style=\"margin-right: 16px; flex-shrink: 0;\"><svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"12\" cy=\"12\" r=\"10\"></circle><line x1=\"15\" y1=\"9\" x2=\"9\" y2=\"15\"></line><line x1=\"9\" y1=\"9\" x2=\"15\" y2=\"15\"></line></svg></div>
  <div class=\"ic-Alert__content\">
    <h5 style=\"font-weight: 700; font-size: 1.125rem; margin-bottom: 8px; color: #a11c1c; margin-top: 0;\">Error</h5>
    <p style=\"margin: 0; color: #a11c1c;\">{safe_msg}</p>
  </div>
</div>
"""
    else:
        alert = f"""
<div class=\"ic-Alert ic-Alert--success\" role=\"alert\" style=\"background-color: #eaf0ea; border: 2px solid #325032; color: #325032; border-radius: 8px; display: flex; align-items: flex-start; padding: 16px; font-family: Montserrat, sans-serif;\">
  <div class=\"ic-Alert__icon\" style=\"margin-right: 16px; flex-shrink: 0;\"><svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M22 11.08V12a10 10 0 1 1-5.93-9.14\"></path><polyline points=\"22 4 12 14.01 9 11.01\"></polyline></svg></div>
  <div class=\"ic-Alert__content\">
    <h5 style=\"font-weight: 700; font-size: 1.125rem; margin-bottom: 8px; color: #325032; margin-top: 0;\">Success</h5>
    <p style=\"margin: 0; color: #325032;\">{safe_msg}</p>
  </div>
</div>
"""

    return f"""
<div style=\"padding: 15px; border: 1px solid #d1d1d1; border-radius: 15px; margin-bottom: 20px; background-color: #ffffff;\">
  <h2>{html.escape(title)}</h2>
  {alert}
  {actions_html}
  <p style=\"margin-top: 20px;\"><a href=\"/\" style=\"display:inline-block;text-decoration:none;text-align:center;padding:10px 12px;border-radius:10px;background-color:#1450A0;color:#fff;border:1px solid #1450A0;font-weight:700;\">Back to Builder</a></p>
</div>
"""


def _strict_validate_text2qti(text: str, *, source_name: str, resource_path: Path) -> tuple[bool, str, dict[str, int | float] | None]:
    config = Config()
    config.load()
    try:
        quiz = Quiz(
            text,
            config=config,
            source_name=source_name,
            resource_path=resource_path.as_posix(),
        )
        QTI(quiz)
    except Text2qtiError as exc:
        return False, str(exc), None

    question_count = sum(isinstance(item, Question) for item in quiz.questions_and_delims)
    group_count = sum(isinstance(item, GroupStart) for item in quiz.questions_and_delims)
    text_region_count = sum(isinstance(item, TextRegion) for item in quiz.questions_and_delims)
    stats = {
        "questions": question_count,
        "groups": group_count,
        "text_regions": text_region_count,
        "points": quiz.points_possible,
    }
    return True, "", stats


def _validation_error_html(validation_error: str, text: str) -> str:
    lines = text.splitlines()
    line_match = re.search(r"on line (\d+):\n(.+)$", validation_error, flags=re.DOTALL)
    if line_match:
        line_number = int(line_match.group(1))
        issue = line_match.group(2).strip()
    else:
        line_number = None
        issue = validation_error.strip()

    hints: list[str] = []
    issue_lower = issue.lower()
    if "missing whitespace after" in issue_lower:
        hints.append("Add required spacing after the marker (for questions, use two spaces after `1.`).")
    if "missing content after" in issue_lower:
        hints.append("Add the missing content after the marker on that line.")
    if "cannot have" in issue_lower and "without a question" in issue_lower:
        hints.append("Move this line directly under its question, or add the missing question line first.")
    if "question must specify a response type" in issue_lower:
        hints.append("Add one response marker under the question (for example `*a)`, `[ ]`, `=`, `*`, `____`, or `^^^^`).")
    if "question must specify a correct choice" in issue_lower:
        hints.append("Mark at least one correct answer with `*` (for example `*b) correct answer`).")

    parts = [
        "Validation failed. Fix the issue below, then run Validate again.",
        f"<b>Issue:</b> {html.escape(issue)}",
    ]
    if line_number is not None:
        parts.append(f"<b>Line:</b> {line_number}")
        if 1 <= line_number <= len(lines):
            line_text = lines[line_number - 1]
            shown = line_text if line_text.strip() else "(blank line)"
            parts.append(f"<b>Line content:</b> <code>{html.escape(shown)}</code>")
    if hints:
        hint_lines = "<br>".join(f"- {html.escape(hint)}" for hint in hints)
        parts.append(f"<b>Suggested fix:</b><br>{hint_lines}")
    parts.append(f"<details><summary>Full parser message</summary><pre>{html.escape(validation_error)}</pre></details>")
    return "<br><br>".join(parts)


def _validation_success_html(stats: dict[str, int | float]) -> str:
    return (
        "Validation passed. This content is correctly formatted for Text2QTI.<br><br>"
        f"<b>Questions:</b> {stats['questions']}<br>"
        f"<b>Question groups:</b> {stats['groups']}<br>"
        f"<b>Text regions:</b> {stats['text_regions']}<br>"
        f"<b>Total points:</b> {stats['points']}"
    )


def _convert_after_validation_form_html(*, validated_text: str, base_name: str) -> str:
    return f"""
<form action=\"/upload\" method=\"post\" enctype=\"multipart/form-data\" style=\"margin-top: 16px;\">
  <textarea name=\"pasted_text\" style=\"display:none;\" aria-hidden=\"true\">{html.escape(validated_text)}</textarea>
  <input type=\"hidden\" name=\"base_name\" value=\"{html.escape(base_name)}\">
  <button type=\"submit\" style=\"display:inline-block;text-decoration:none;text-align:center;padding:10px 12px;border-radius:10px;background-color:#1450A0;color:#fff;border:1px solid #1450A0;font-weight:700;\">Convert This Validated Text to QTi</button>
</form>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            body = _home_body()
            data = _page("Canvas Quiz Builder", body)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {"/upload", "/validate"}:
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return
        submit_action = "validate" if self.path == "/validate" else "convert"

        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            data = _page("Canvas Quiz Builder", _result_body("Request Failed", "Invalid form submission.", True))
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0:
            data = _page("Canvas Quiz Builder", _result_body("Request Failed", "Empty submission.", True))
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        body = self.rfile.read(content_length)
        parser = BytesParser(policy=policy.default)
        msg = parser.parsebytes(
            b"Content-Type: " + content_type.encode("utf-8") + b"\r\n"
            b"MIME-Version: 1.0\r\n\r\n" + body
        )

        pasted_text = None
        base_name = None
        if msg.is_multipart():
            for part in msg.iter_parts():
                if part.get_content_disposition() != "form-data":
                    continue
                name = part.get_param("name", header="content-disposition")
                if name == "pasted_text":
                    pasted_text = (part.get_content() or "").strip()
                elif name == "base_name":
                    base_name = (part.get_content() or "").strip()

        if not pasted_text:
            data = _page("Canvas Quiz Builder", _result_body("Request Failed", "No quiz text was provided.", True))
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        safe_base = re.sub(r"[^a-zA-Z0-9._-]+", "-", base_name or "quiz").strip("-") or "quiz"
        filename = f"{safe_base}.txt"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_path = tmpdir_path / filename
            input_path.write_text(pasted_text, encoding="utf-8")

            if submit_action == "validate":
                valid, validation_error, stats = _strict_validate_text2qti(
                    pasted_text,
                    source_name=input_path.as_posix(),
                    resource_path=tmpdir_path,
                )
                if not valid:
                    msg_html = _validation_error_html(validation_error, pasted_text)
                    data = _page("Canvas Quiz Builder", _result_body("Validation Failed", msg_html, True, allow_html=True))
                    self.send_response(HTTPStatus.BAD_REQUEST)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return

                success_html = _validation_success_html(stats)
                convert_form_html = _convert_after_validation_form_html(
                    validated_text=pasted_text,
                    base_name=safe_base,
                )
                data = _page(
                    "Canvas Quiz Builder",
                    _result_body(
                        "Validation Complete",
                        success_html,
                        False,
                        allow_html=True,
                        actions_html=convert_form_html,
                    ),
                )
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            if not VENV_TEXT2QTI.exists():
                data = _page(
                    "Canvas Quiz Builder",
                    _result_body("Conversion Failed", "text2qti is not installed in .venv. Run: .venv/bin/python -m pip install .", True),
                )
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            result = subprocess.run(
                [str(VENV_TEXT2QTI), str(input_path)],
                text=True,
                capture_output=True,
            )

            if result.returncode != 0:
                msg = result.stderr.strip() or "text2qti failed."
                msg_html = f"Text2QTI conversion failed:<br><pre>{html.escape(msg)}</pre>"
                data = _page("Canvas Quiz Builder", _result_body("Conversion Failed", msg_html, True, allow_html=True))
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            output_zip = input_path.with_suffix(".zip")
            if not output_zip.exists():
                data = _page("Canvas Quiz Builder", _result_body("Conversion Failed", "Expected output .zip was not created.", True))
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            desktop = Path.home() / "Desktop"
            desktop.mkdir(parents=True, exist_ok=True)
            dest = desktop / output_zip.name
            if dest.exists():
                stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
                dest = desktop / f"{output_zip.stem}-{stamp}{output_zip.suffix}"

            shutil.move(str(output_zip), str(dest))

        msg = f"Saved to Desktop: {dest}"
        data = _page("Canvas Quiz Builder", _result_body("Conversion Complete", msg, False, allow_html=True))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run() -> None:
    server = HTTPServer(("127.0.0.1", 8001), Handler)
    print("Canvas Quiz Builder running at http://localhost:8001")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
