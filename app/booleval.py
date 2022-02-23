import sys
import re

default_token = {
    'True'  : True,
    'False' : False,
    '&&'    : lambda left, right: left and right,
    '||'    : lambda left, right: left or right,
    '('     : '(',
    ')'     : ')'
}

empty = True


def _find(token, what, start=0):
    return [n for n, x in enumerate(token) if x == what and n >= start]

def _parens(token):
    """
        Returns: (bool)parens_exist, left_paren_pos, right_paren_pos
    """
    item = _find(token, '(')

    if not item:
        return False, -1, -1

    left = item[-1]

    #can not occur earlier, hence there are args and op.
    right = _find(token, ')', left + 4)[0]

    return True, left, right

def create_token(s, default_token=default_token):
    """
        Create token list: 'True or False' -> [True, lambda..., False]
    """
    s = re.sub(r'([^\&\|])\)', r'\1 )', re.sub(r'\(([^\&\|])', r'( \1', re.sub(r'\&\&', ' && ', re.sub(r'\|\|', ' || ', re.sub(r'\s+', '', s)))))

    return [x not in default_token and x or default_token[x] for x in s.split() if x]

def bool_eval(token):
    """
        Token_lst has length 3 and format: [left_arg, operator, right_arg]
        operator(left_arg, right_arg) is returned
    """
    return token[1](token[0], token[2])

def formatted_bool_eval(token, empty=empty):
    """
        Eval a formatted (i.e. of the form 'ToFa(ToF)') string
    """
    if not token:
        return empty

    if len(token) == 1:
        return token[0]

    has_parens, left, right = _parens(token)

    if not has_parens:
        if len(token) == 3:
            return bool_eval(token)
        else:
            token[:3] = [bool_eval(token[:3])]
    else:
        token[left:right+1] = [bool_eval(token[left+1:right])]

    return formatted_bool_eval(token, bool_eval)

def nested_bool_eval(token):
    """
        The actual 'eval' routine,
        if 's' is empty, 'True' is returned,
        otherwise 's' is evaluated according to parentheses nesting.
        
        The format assumed:
        [1] 'LEFT OPERATOR RIGHT',
        where LEFT and RIGHT are either:
                True or False or '(' [1] ')' (subexpression in parentheses)
    """
    return formatted_bool_eval(create_token(s))


class Token:

    def __init__(self):
        self.source = ''
        self.token = []
        self.eval_token = []
        self.is_evaluated = False

    def _init_state(self, source):
        self.source = source
        self.token = create_token(source)
        self.is_evaluated = False

    def __call__(self):
        if not self.is_evaluated:
            return False
        return formatted_bool_eval(self.eval_token)

    def get_token(self):
        return self.token

    def get_source(self):
        return self.source

    def is_key(self, x):
        return not (callable(x) or x in '(||&&)')

    def get_keys(self, case_insensitive=False):
        keys = []
        n = 0
        for x in self.token:
            if self.is_key(x):
                n += 1
                keys.append({
                    'id'    : 'x%d' % n,
                    'value' : case_insensitive and x.lower() or x,
                    'res'   : None,
                })
        return keys

    def set_values(self, values=None):
        if not values:
            return
        token = []
        n = 0
        for x in self.token:
            if self.is_key(x):
                value = n < len(values) and values[n]['res'] and True or False
                token.append(value)
                n += 1
            else:
                token.append(x)
        self.eval_token = [x for x in token]
        self.is_evaluated = True

    def check(self):
        return formatted_bool_eval(self.token)


def new_token():
    return Token()


if __name__ == "__main__":
    argv = sys.argv

    if len(argv) < 2 or argv[1].lower() in ('/h', '/help', '-h', 'help', '--help'):
        pass
    else:
        token = new_token()

        while True:
            s = input('>>> Type expression:')
            
            print('--> %s' % s)
            
            if s == 'quit':
                break
        
            token._init_state(s)
        
            print('--> ' + repr(token.get_token()) + ' : ' + repr(token.check()))
