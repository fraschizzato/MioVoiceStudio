from app.tts import split_text

def test_short():
    assert split_text('Ciao mondo.',100)==['Ciao mondo.']

def test_long_no_loss():
    text='Prima frase. Seconda frase abbastanza lunga. Terza frase.'
    chunks=split_text(text,25)
    assert all(len(x)<=25 or ' ' not in x for x in chunks)
    assert 'Prima frase.' in ' '.join(chunks)
