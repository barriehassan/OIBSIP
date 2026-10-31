"""Password Lab presentation and ephemeral input lifecycle, separate from generation."""
import tkinter as tk
from app.core.password_lab import evaluate_password, generate_replacement

WHITE = '#F4F7FF'
MUTED = '#C0D1F1'
CYAN = '#6CCBFF'
COLORS = ('#FF9BAA', '#FFB698', '#F4D28D', '#6CCBFF', '#3CE9B0')


class PasswordLabView:
    def __init__(self, app):
        self.app = app
        self.value = tk.StringVar(master=app)
        self.visible = False
        self.pending = None
        self.assessment = evaluate_password('')
        self.entry = tk.Entry(app.canvas, textvariable=self.value, show='*',
            bg='#DDE8FF', fg='#102454', insertbackground='#102454',
            relief='flat', bd=0, exportselection=False)
        # Bound paste/type size without truncating and mis-scoring a prefix.
        self.entry.configure(validate='key', validatecommand=(app.register(lambda value: len(value) <= 4096), '%P'))
        self.value.trace_add('write', self._changed)

    def _changed(self, *_):
        if self.pending:
            self.app.after_cancel(self.pending)
            self.pending = None
        self.assessment = evaluate_password('')
        if self.app.nav == 'Password Lab':
            self.pending = self.app.after(180, self._evaluate)
            self.app._draw()

    def _evaluate(self):
        if self.pending:
            self.app.after_cancel(self.pending)
        self.pending = None
        if self.app.nav != 'Password Lab':
            return
        self.assessment = evaluate_password(self.value.get())
        self.app._draw()

    def clear(self):
        if self.pending:
            self.app.after_cancel(self.pending)
            self.pending = None
        self.value.set('')
        # The write trace may schedule a new callback while still on this page.
        if self.pending:
            self.app.after_cancel(self.pending)
            self.pending = None
        self.visible = False
        self.entry.configure(show='*')
        self.assessment = evaluate_password('')

    def leave(self):
        self.clear()
        if hasattr(self.entry, '_canvas_item'):
            self.app.canvas.itemconfigure(self.entry._canvas_item, state='hidden')
        self.entry.selection_clear()
        self.app.canvas.focus_set()

    def toggle(self):
        self.visible = not self.visible
        self.entry.configure(show='' if self.visible else '*')
        self.app._draw()

    def replace(self):
        # Does not touch generator state, settings, history, or automatic copy.
        self.visible = False
        self.value.set(generate_replacement())
        if self.pending:
            self.app.after_cancel(self.pending)
            self.pending = None
        self._evaluate()

    def draw(self):
        a, result = self.app, self.assessment
        a._text(290,222,'Password Lab',22,bold=True)
        a._text(290,255,'Up to 72 characters. Analysis stays on this device.',13,MUTED)
        a._rect((290,289,976,353),'#DDE8FF','#D4E5FF')
        self.entry.configure(font=(a.mono_font,-max(16,round(23*a.scale))),show='' if self.visible else '*')
        a._embed(self.entry,306,301,476,38)
        a._button((798,299,877,342),'Hide' if self.visible else 'Show',self.toggle)
        a._button((887,299,964,342),'Clear',self._clear_clicked)
        a._button((290,378,699,429),'Generate a fresh replacement',self.replace,primary=True)
        a._text(716,382,'Independent random password.\nNever a predictable suffix.',12,MUTED,width=250)
        color=COLORS[result.score] if result.score is not None else CYAN
        a._text(1042,222,'Estimated strength',21,bold=True)
        a._text(1043,276,result.rating,28,color,True)
        a._rect((1044,326,1394,338),'#496797',radius=5)
        if result.progress:
            a._rect((1044,326,1044+350*result.progress,338),color,radius=5)
        a._text(1044,360,'Local pattern-based estimate.\nNo breach database check.\nNo guarantee of security.',13,MUTED,width=345)
        a._text(290,496,'Input profile & policy',21,bold=True)
        a._text(290,538,f'Length: {result.length} characters',16,bold=True)
        composition=', '.join(result.composition) if result.composition else 'None / not analyzed'
        a._text(290,573,'Character types: '+composition,14,MUTED,width=460)
        a._text(290,632,'Generator policy (separate from strength)',14,bold=True)
        policy=('Meets the generator rules: 8 to 64 characters,\nat least two character categories.'
                if result.policy_compliant else '\n'.join(result.policy_notes))
        a._text(290,665,policy,13,MUTED,width=460)
        a._text(290,755,'Composition describes the input.\nPassing these rules does not make it strong.',13,CYAN,width=460)
        a._text(832,496,'Findings & next steps',21,bold=True)
        # Scrollable text prevents long feedback from overflowing at small sizes.
        if not hasattr(self,'feedback'):
            self.feedback=tk.Text(a.canvas,bg='#203A6A',fg=WHITE,relief='flat',bd=0,
                wrap='word',padx=12,pady=10,takefocus=True,exportselection=False)
        self.feedback.configure(state='normal',font=(a.ui_font,-max(12,round(15*a.scale))))
        self.feedback.delete('1.0','end')
        sections=['FINDINGS']+[f'- {issue}' for issue in result.issues]
        if not result.issues:sections+=['- Type a password to see its assessment.']
        sections+=['','RECOMMENDATIONS']+[f'- {tip}' for tip in result.recommendations]
        self.feedback.insert('1.0','\n'.join(sections))
        self.feedback.configure(state='disabled')
        a._embed(self.feedback,832,539,564,251)
        a._text(288,851,'Private session: no saving, no history, no upload. Input clears when you leave Password Lab.',13,MUTED,width=1100)
        a._draw_focus()

    def _clear_clicked(self):
        self.clear()
        self.app._draw()
