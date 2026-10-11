use crate::codebook::CODEBOOK;

const NONE: u16 = 256;

#[derive(Clone, Copy)]
struct Pair {
    code: u16,
    longer: u16,
}

struct Lookup {
    single: [u16; 128],
    pairs: [Pair; 128 * 128],
    next: [u16; 254],
}

const fn make_lookup() -> Lookup {
    let mut lookup = Lookup {
        single: [NONE; 128],
        pairs: [Pair {
            code: NONE,
            longer: NONE,
        }; 128 * 128],
        next: [NONE; 254],
    };
    let mut code = 0;
    while code < CODEBOOK.len() {
        let word = CODEBOOK[code];
        if word.len() == 1 {
            lookup.single[word[0] as usize] = code as u16;
        } else {
            let key = word[0] as usize * 128 + word[1] as usize;
            if word.len() == 2 {
                lookup.pairs[key].code = code as u16;
            } else {
                lookup.next[code] = lookup.pairs[key].longer;
                lookup.pairs[key].longer = code as u16;
            }
        }
        code += 1;
    }
    lookup
}

static LOOKUP: Lookup = make_lookup();

#[inline]
fn longest_match(input: &[u8]) -> Option<(u8, usize)> {
    let first = input[0] as usize;
    if first >= 128 {
        return None;
    }
    let mut code = LOOKUP.single[first];
    let mut length = usize::from(code != NONE);
    if input.len() >= 2 && input[1] < 128 {
        let pair = LOOKUP.pairs[first * 128 + input[1] as usize];
        if pair.code != NONE {
            code = pair.code;
            length = 2;
        }
        let mut candidate = pair.longer;
        while candidate != NONE {
            let word = CODEBOOK[candidate as usize];
            if word.len() > length && input.starts_with(word) {
                code = candidate;
                length = word.len();
            }
            candidate = LOOKUP.next[candidate as usize];
        }
    }
    (code != NONE).then_some((code as u8, length))
}

#[inline]
fn flush_literals(output: &mut Vec<u8>, literals: &[u8]) {
    match literals.len() {
        0 => (),
        1 => output.extend_from_slice(&[254, literals[0]]),
        length => {
            output.extend_from_slice(&[255, (length - 1) as u8]);
            output.extend_from_slice(literals);
        }
    }
}

pub(crate) fn compress(input: &[u8]) -> Vec<u8> {
    let mut output = Vec::with_capacity(input.len() + input.len() / 128 + 2);
    let mut position = 0;
    let mut literal_start = 0;
    while position < input.len() {
        if let Some((code, length)) = longest_match(&input[position..]) {
            flush_literals(&mut output, &input[literal_start..position]);
            output.push(code);
            position += length;
            literal_start = position;
        } else {
            position += 1;
            if position - literal_start == 256 {
                flush_literals(&mut output, &input[literal_start..position]);
                literal_start = position;
            }
        }
    }
    flush_literals(&mut output, &input[literal_start..]);
    output
}

pub(crate) fn decompress(input: &[u8]) -> Result<Vec<u8>, &'static str> {
    let mut output = Vec::with_capacity(input.len().saturating_mul(2));
    let mut position = 0;
    while position < input.len() {
        let code = input[position];
        position += 1;
        match code {
            254 => {
                let byte = input.get(position).ok_or("truncated SMAZ literal byte")?;
                output.push(*byte);
                position += 1;
            }
            255 => {
                let length =
                    *input.get(position).ok_or("truncated SMAZ literal length")? as usize + 1;
                position += 1;
                let end = position + length;
                let literal = input
                    .get(position..end)
                    .ok_or("truncated SMAZ literal run")?;
                output.extend_from_slice(literal);
                position = end;
            }
            _ => output.extend_from_slice(CODEBOOK[code as usize]),
        }
    }
    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_codebook_entry() {
        for (code, word) in CODEBOOK.iter().enumerate() {
            assert_eq!(compress(word), [code as u8]);
            assert_eq!(decompress(&[code as u8]).unwrap(), *word);
        }
    }

    #[test]
    fn literal_boundaries() {
        for length in [0, 1, 2, 255, 256, 257, 512, 513, 4096, 65536] {
            let input = vec![0x80; length];
            let encoded = compress(&input);
            assert_eq!(decompress(&encoded).unwrap(), input);
            if length == 256 {
                assert_eq!(&encoded[..2], &[255, 255]);
            }
        }
    }

    #[test]
    fn arbitrary_bytes() {
        let input: Vec<u8> = (0..=255).cycle().take(65536).collect();
        assert_eq!(decompress(&compress(&input)).unwrap(), input);
    }

    #[test]
    fn truncated_literals() {
        for input in [&[254][..], &[255], &[255, 0], &[255, 2, 1, 2]] {
            assert!(decompress(input).is_err());
        }
    }
}
