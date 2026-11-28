"""Split the combined response into one self-contained reply per reviewer. Usage: python3 -I split_response.py response_R1.md"""
import sys
t=open(sys.argv[1],encoding='utf8').read()
body=t.split('---\n',2)[2]
i_sum=body.index('## Summary of the main changes'); i_ai=body.index('## Use of generative AI in this revision'); i1=body.index('# Reviewer 1'); i2=body.index('# Reviewer 2'); i3=body.index('# Reviewer 3')
head=body[:i_sum]; summ=body[i_sum:i_ai].strip(); ai=body[i_ai:i1].strip(); R={1:body[i1:i2],2:body[i2:i3],3:body[i3:]}
ms=[l for l in head.strip().split('\n\n') if l.startswith('**Manuscript') or l.startswith('**Previous') or l.startswith('**Journal')]
intro={1:"We thank the reviewer for a careful and constructive report. The reviewer examined our public code and results, and every statement of fact in the report that we could check was correct. We have corrected the manuscript accordingly, and we say plainly below where our submitted text claimed more than the data support.",
       2:"We thank the reviewer for a careful and constructive report. We agree with the main concern, that the objectives, the analyses and the conclusions needed to be brought into line, and the manuscript has been restructured for that purpose.",
       3:"We thank the reviewer for a careful and constructive report. The requests to check the references and to clarify the status of the analysis plan each led to a correction that we would not otherwise have made."}
ai_short="## Use of generative AI\n\nGenerative AI (Claude, Anthropic) was used as a tool in the first draft and in this revision, including the drafting of these responses, under the authors' direction. The authors reviewed and edited the output and take full responsibility for it. Section 2.10 and the Acknowledgments of the manuscript describe this use in full."
a="While checking the references for Reviewer 3 we found that the reference we had used for miR-221/222 has been retracted (see Reviewer 3, comment 4)."
assert a in R[2]
R[2]=R[2].replace(a,"While checking all references in this revision we found that the reference we had used for miR-221/222 (Zhao et al., *J. Biol. Chem.* 2008) was retracted in 2016. It has been removed and replaced by an independent study (Di Leva et al., *J. Natl. Cancer Inst.* 2010), and the Supplementary Note says so. Neither microRNA differed between tumour and normal tissue, so no result depended on it.")
a="Please see the statement at the start of this letter."; assert a in R[3]
R[3]=R[3].replace(a,"Please see the statement above, under \"Use of generative AI in this revision\".")
ai3=ai.replace("Reviewer 3 asked for a complete statement.","The reviewer asked for a complete statement.")
for n in (1,2,3):
    sec=R[n].replace(f"# Reviewer {n}\n","## Point-by-point responses\n",1)
    doc=f"---\ntitle: \"Response to Reviewer {n}\"\n---\n\n"+"\n\n".join(ms)+f"\n\n{intro[n]}\n\nSection numbers refer to the revised manuscript. Changes are shown with Track Changes in the marked copy. The reviewer's comments are in italics.\n\n{summ}\n\n{ai3 if n==3 else ai_short}\n\n{sec.strip()}\n"
    for m in (1,2,3):
        if m!=n: assert f'Reviewer {m}' not in doc, (n,m)
    open(f'response_R1_reviewer{n}.md','w',encoding='utf8').write(doc); print(n,len(doc.split()))
