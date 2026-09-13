import re, sys
src = open('pbt_argos.tex').read()
lines = src.split('\n')

# header: everything up to and including the title frame (which ends with "\end{frame}}")
hdr_end = next(i for i,l in enumerate(lines) if l.startswith('\\end{frame}}'))
header = '\n'.join(lines[:hdr_end+1])
body = '\n'.join(lines[hdr_end+1:])

# extract frames (non-greedy), keyed by title
frames = {}
order_seen = []
for m in re.finditer(r'\\begin\{frame\}(.*?)\\end\{frame\}', body, re.S):
    block = m.group(0)
    head = m.group(1)
    tm = re.match(r'\s*(?:\[[^\]]*\])?\s*\{(.*?)\}\s*\n', head, re.S)
    title = re.sub(r'\s+', ' ', tm.group(1)).strip() if tm else '<untitled>'
    key = title
    if key in frames:  # duplicate titles (PET range verification x2)
        key = title + ' #2'
    frames[key] = block
    order_seen.append(key)
print('frames found:', len(order_seen), file=sys.stderr)
for k in order_seen: print('  ', k, file=sys.stderr)

# fix the stray "//" in the market-share footnote
frames['Market Share'] = frames['Market Share'].replace('excluded.//', 'excluded.\\\\')
k = 'Development programme and investment'
f = frames[k]
f = f.replace('{Development programme and investment}', '{Development programme}')
f = f.replace(r'''\textbf{Investment: approximately \hi{\euro1 million per year}, or \hi{\euro3--4 million in total}.}
\par\vspace{5mm}
''', '')
assert 'Investment:' not in f, 'investment line not removed'
frames['Development programme'] = f
del frames[k]

def divider(num, title, sub):
    return (r"""\begin{frame}[plain,noframenumbering]
\centering
\vspace{1.6cm}
{\color{crBlue}\rule{0.55\textwidth}{1.1pt}}\\[6mm]
{\Large\color{crGrey} %s}\\[4mm]
{\Huge\bfseries\color{crBlue} %s}\\[6mm]
{\color{crBlue}\rule{0.55\textwidth}{1.1pt}}
\end{frame}""" % (num, title))

plan = [
 ('I', 'Proton therapy and the range problem',
  'Why the physical advantage of protons is limited by where the beam actually stops', [
   'What is proton therapy?',
   'Example: Brain tumours',
   'From treatment planning to delivery',
   'Why range uncertainty matters',
   'The Proton Therapy Paradox',
   'Range uncertainty is a clinically relevant limitation',
   'What could better range verification change?',
 ]),
 ('II', 'In-vivo range verification',
  'Measurement principles, twenty years of clinical experience, and why it is not yet routine', [
   'Boosting proton therapy',
   'Complementary imaging for proton therapy',
   'PET: an \\emph{in vivo} probe of where the beam stopped',
   'PET range verification: offline, in-beam and in-room',
   'PET range verification: offline, in-beam and in-room #2',
   'Offline results in large uncertainties',
   'Online/In-room tradeoffs',
   'Prompt gammas: tracking the proton range during irradiation',
   'Imaging prompt gammas with a Compton camera',
   'PET and Compton imaging: complementary measurements',
   'Two decades of in-vivo verification: what have we learned?',
   'Why has in-vivo verification not become routine?',
   'In-vivo verification: towards intervention',
   'Reaction from the Industry',
 ]),
 ('III', 'CRYSP and COCOA',
  'Cryogenic PET and a compact Compton camera: high sensitivity at low cost', [
   'CRYSP: PET with cryogenic cesium iodide',
   'CRYSP: \\emph{CRYogenic Sensitive PET}',
   'COCOA: a compact Compton camera for MeV gamma rays',
   'COCOA: demonstrated scalability and efficiency',
   'Reference protocol: all scanner configurations are sub-mm',
   'Scanner cost breakdown',
   'Total scanner cost',
 ]),
 ('IV', 'The proton-therapy market',
  'Deployment, clinical evidence, market size and industry structure', [
   'Proton therapy: worldwide deployment and growth in Europe',
   'Proton therapy adoption',
   'Clinical evidence for proton therapy',
   'Clinical evidence approaching an inflection point',
   'Market Size: The Vision of Independent Consultants',
   'Market Share',
   'Market dynamics and Prospectives',
 ]),
 ('V', 'ARGOS',
  'Team, vision, development programme and economics', [
   'The DIPC group',
   'CRYSP and COCOA for proton beam monitoring',
   'Our vision: an integrated monitoring service',
   'Main Challenges Ahead',
   'Development programme',
   '@@COSTS@@',
 ]),
]

out = [header, '',
 '% Colours used by the market and clinical-evidence slides (defined once).',
 r'\definecolor{PTblue}{RGB}{25,78,125}',
 r'\definecolor{PTred}{RGB}{145,45,55}',
 r'\definecolor{PTgray}{RGB}{80,90,105}', '']
used = set()
for num, title, sub, keys in plan:
    out.append('%' + '='*76)
    out.append('%% PART ' + num + ': ' + title)
    out.append('%' + '='*76)
    out.append(divider(num, title, sub)); out.append('')
    for k in keys:
        if k == '@@COSTS@@':
            out.append('% Six economics and market slides generated from the CSV models in costs/.')
            out.append(r'\input{costs/slides.tex}'); out.append('')
            continue
        if k not in frames:
            sys.exit('missing frame: ' + k)
        used.add(k)
        out.append(frames[k]); out.append('')
out.append(r'\end{document}')

unused = [k for k in order_seen if k not in used]
print('unused frames (dropped):', unused, file=sys.stderr)
open('pbt_argos_v2.tex','w').write('\n'.join(out))
print('wrote pbt_argos_v2.tex', file=sys.stderr)
