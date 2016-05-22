\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{SciPost} % SciPost Latex Template v1.1 (2016/05/22)


\LoadClass[10pt]{article}


% Layout
\RequirePackage{a4}
\RequirePackage[top=10mm,bottom=10mm,left=16mm,right=16mm,head=10mm,includeheadfoot]{geometry}
\bigskipamount 6mm


% Unicode characters
\RequirePackage[utf8]{inputenc}

% doi links in references
\RequirePackage{doi}

% Math formulas and symbols
\RequirePackage{amsmath,amssymb}

% Hyperrefs
\RequirePackage{hyperref}

% Include line numbers in submissions
\RequirePackage{lineno}

% SciPost BiBTeX style
\bibliographystyle{SciPost_bibstyle_v1}

% SciPost header and footer
\RequirePackage{fancyhdr}
\pagestyle{fancy}

\RequirePackage{xcolor}
\definecolor{scipostdeepblue}{HTML}{002B49}


\lhead{
  \colorbox{scipostdeepblue}{\strut \bf \color{white} ~Submission }
}

\rhead{
  \colorbox{scipostdeepblue}{\strut \bf \color{white} ~SciPost Physics }
}

\DeclareOption{LectureNotes}{
  \rhead{
    \colorbox{scipostdeepblue}{\strut \bf \color{white} ~SciPost Physics Lecture Notes }
  }
}
\ProcessOptions\relax

