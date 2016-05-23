\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{SciPost} % SciPost Latex Template v1.1 (2016/05/22)


\LoadClass[10pt]{article}


% Layout
\RequirePackage[top=12mm,bottom=12mm,left=24mm,right=24mm,head=12mm,includeheadfoot]{geometry}
\bigskipamount 6mm

% For table of contents: remove trailing dots
\RequirePackage{tocloft}
\renewcommand{\cftdot}{}
% Add References to TOC
\RequirePackage[nottoc,notlot,notlof]{tocbibind}


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
\bibliographystyle{SciPost_bibstyle_v1-1}

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

