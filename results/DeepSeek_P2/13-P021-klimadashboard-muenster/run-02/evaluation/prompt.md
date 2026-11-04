# Role

You are an impartial evaluator assessing the documentation quality of a software installation guide.

# Task

Evaluate the supplied installation guide using the criteria and rating scale
below. For each criterion, assign one score from 1 to 5 and provide a brief
reason for your score.

# Evaluation instructions

- Review the complete installation guide before assigning any scores.
- Use only information contained in the installation guide as evidence.

# Criteria and rating scale

```json
{
  "rating_scale": [
    {
      "score": 1,
      "label": "Very poor"
    },
    {
      "score": 2,
      "label": "Poor"
    },
    {
      "score": 3,
      "label": "Adequate"
    },
    {
      "score": 4,
      "label": "Good"
    },
    {
      "score": 5,
      "label": "Excellent"
    }
  ],
  "criteria": {
    "completeness": "How would you rate the guide's coverage of the information needed to install, configure where required, and verify the software?",
    "structure": "Is the installation guide arranged so that the user can find what is needed and follow the installation process in the required order?",
    "clarity": "Are instructions, commands, prerequisites, configuration values, and expected outcomes stated precisely and without ambiguity?",
    "understandability": "How easy was it to understand the installation or setup steps? Consider whether the guide explained the technical terms and concepts or required you to know them beforehand."
  }
}
```

# Evaluation procedure

For each criterion:

1. Read the criterion name and its evaluation question.
2. Determine how well the guide meets the criterion described by the question.
3. Select one score from 1 to 5 using the rating scale.
4. Provide a brief reason for the score using evidence from the guide.

# Installation guide

## Getting Started

To run the Klimadashboard application on your local machine, first clone the repository:

> git clone https://github.com/your-username/klimadashboard.git
> cd klimadashboard

Then, install the dependencies:

> yarn install

Finally, start the development server:

> yarn dev

You should now be able to access the application at `http://localhost:3000`.
