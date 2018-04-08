#!/usr/bin/env python
import requests
# feel free to change this line
from secrets import username, password

def login(username, password):
    '''(str, str) -> requests.RequestsCookieJar
    Note that username and password should NOT be url-encoded'''
    authsite = 'https://cas.auth.sc.edu/cas/login'
    data = {'username': username, 'password': password, 'idtype': 'generic',
            'lt': 'LT-112241-hRbaeEbSLjbxGx3Jzmv1aiVD2q4ca7',
            '_eventId': 'submit', 'submit': 'LOGIN',
            'execution': "a0ecef29-ae7e-4bb4-9a31-cbb04b6f42bf_ZXlKaGJHY2lPaUpJVXpVeE1pSjkuYW1ad1JHNWxWV0pEZUdKaGRFWnFWMmxhVEd4alFsbzFWak42VTFGaFYwbHdPVGN4UVhKalJXTk9Ra2wzY1VOdlF6QnVhalI2VFUxbVNISmpVQ3N6WlM5b05FRkRSMkZaVkVKaVZXMUNiR3RWWjFGTU5tRkRabWc0UjBVelprMUdNM1JJUmtOM1V6TnJLMUY2ZDNCT1JtWmxkRVpvYW01dVMyUkhWbVJrTW0xQ1JFeDRUVGhSYkdWRlNIRk5TbWQ0WlhaaWJXVnZjVk00VlROeVQySTJRVXBrYjBRNGNFcDViVE12VTJKeE5tWktZbTFaYVc1T2VsSk9OMEo0UkdOd05IUktSRkI1WmpodlFreENRbk5DTmpCcFRXaHNZVVp6TlVOa0t6RTNhSEUzYnpSRE5USkhZMmh4V0c5T1JVeEZUMHc1V1RKemNIVTVjazFHSzJ0WFEzUXlNbmhGWXpaMWRrWjRNRGR2Y0hSVVIxWTBiVlJ4Y21KS2JGVmpRVGhHTVVSMVUzVlJSbkpKVDJGWGFXZE5UbVkxYWxaSGNsTjJOa1IyTlV0NGVuSnRUelJOWkRKQlUwRndkMnMwU2tvM00yUm1OSFI1TDNOUlQwczNlR0YzWmpJNGNUTXhNbTVNU3k5d1VWRXdSbGRGTVdkVldYQnliREZoYVd4RFpEUklXbEpzYm5Gc1RqTnZkMVV4YVdVeVJGRnNkekZIZFZrdkwxY3dWMGxTT0ZObmIxRXdORVJYYkVReWNHOVFObkFyTVV0R2FXcHVaRlphTjA1ck1WVk9MMlo1U3poUVdYZExWWFpLTUVoeFZ6ZERPR1JGZUdWTGMyWkhibVJhZWtwM2RqRkpPSHAzZHpCaWREaFVRMGhDU1hrck9Ya3lUWHBXU0c5bVYzSXZWbFJsVHlzelNVUjVkMVZHYkRObFRWSlVRMDB4VUZkT2FWbENNV2cwYlRaUU1VdEtUWFpNTldGallVaHRlbkp6Y2xRMU9XUldXbXROTkd4eVFqVnhaV0puZG1vMFJYTkJjVE5YU0c1SVVDOUhUMFJHZDBscWJUUkNlbmx3Tld0RE16SnpTVEJQT0dwdVIyOHJSMjgzTDFCNFVIVXZRelpRZEhaMGFVeDBTbEJoY1ZkUFltaHVkVlpzVnpGd1VWUklXVlJtYkZwalVEWlBMMFpLZEdGVEwwOXVMMll5Y3pVellqbEJWM2xyVFZWeGVqRnpkbk5ZVG1wcVNrOUZjemx4VkM5WldWY3dRa2MyYWpFMk0wTmtTMncwVGpOc1ZrcFZOVzA1TVNzck0yUm9RemhFTURWNFR6aDBXVXd6TkdGaEx6QmtlRzlrUzJOek1FeHdlQzl4TURRM1dYUm1kMXByT1V0YWQyVnBURTVwZEZneVdETnRkMDlYVUc5RVdVWlJUVW8zV0RoR1EyUXdZMkZXZW00eGVWUTFWVlZxU2tkdU1qRXlRWFZOUlZsd1NIQXJZWFEyVlZGblRWaE9ORGhxYVRobFUwTmFOSEUwUldKV05USnhZek5OUVZZNWMyeEJibVZzV0ZKNFYxTm9NWGxLVkVFNWRrRnRjV1l6Y25aSlFVaFFSbGw0U0c1M1lsbGlOakJOU0V4MWFVdE5lRzVrYUdSc01HUlRkRko2TWpKMGJYRnhSMmRPV25CQk0yODFkbEE0T1RsM1VVUlhaa3hMYUhBeldGZGtaMkp3YmxsV1JHNHpNVWc0Tmk5VlZYTmxSVGRNTDB0UWFWVjRTRXRTYTFaVlNrTXJTRmN6WTBGMmJYbFhWVWQzYVRBNFNEa3lXWFZ6UTNFME0xVk1WQzlCVTFCQllXOUxlWGROVmxaQ1ZFbEpjMDV1ZUdKdmNEbDRNbmh3UWpSVlIyWktkV1ZzTUdOaE5HMDBRWEp3V1hZck1GaGFRWFJZUkVJNVltbEVOV2ROY2pWc1dGTkhLMFUxVlVRME5WcERhbHBPWjIxaldVcFBXUzh4YlVjd0wxWkNablpQTm1wQlVubHdjM2hRVWpRclZqTmhOV0paWWt0MVdGSXhjV0pXYTFOM1VYUm9lRGN4YXk5Sk9TOW1ibmhLVm0xelMxWnZiMjB3VFdSQ2RGUXlWa2xvUVdkV1VuWmtZamxhU201Q1RYbG1kVWxzWjNsSVJsRm5NazB6YlRKa2VXNWtkV05sVlROM1ZISTVLM1JWVDNSMFdqTm1VWGhyVUZWaWVVbE9VUzlDTm0xYU4yTkxURGhGZW1GeVFuRm9WbUV4UTBSMWFrUjZkR3BuZDNKb1VsZE5SM1YzV0ZFeE15dEpMelpZT1RGQ2VHOTFOVkpaYUhsV1dHVXZXbW8wVDFWbE16TllVVVphT1ZacGVUUmFSa2hxVkhsdVJsUlBUM1pFVmxFeWNGbHhUVTVuWkdKQ2VYcFZXRWhMSzFwa2FrbHhXSFIxVG1KUFdHWndiRWhoUjBwQmMxQkhOMkZ3YjFoa1lYVk1hVTg1U1VwbVdHNHdjRTFZWmtWcE1uTklSV1JMTUd3ck9UTXpUSE0zTHpCa2JWUkdjVEprYlc1RVN6aDFVMlpXVVdFdlJDOVhiV3g0VERWNVJsaEZRMmRMUmt4b1ZUWm5ZMHBWWlVaTFVEVlZVR1p6UzFKS2FuQmtNMng2YmxSTFRETlBjM1JuZWs5dlRuVTJTSGRVT1ZoMGRsSlhaVUpsU0RoTVJUaEhLelV6U2pOd1EwYzJiRGhJY1VkUlNIcFpkQzlXY0VZek5saFJiSFp4WkRkMmMxZGFZa1puUlVJNFdGSnJUbTUwTW01R2JHRnlhMUJwWW1kTFluazRMMk5QUkhsVmRrZzRURm8yVW1KTWNWUXlUblphUzJGdmVVVjBjSHBMU0VkRlkzQlJaRTB2YUVoMlJIQkNNSGxFTUc5Uk1qWTNVVkp1Wm5aRWNrTmxWV2xNT0N0aFIzVjJMMHB2WkZSalNXUktSVUpZUW5GWllVUmhTbXBVWTBwWFR5OXpVbWhUVkRGSmNsRlhUSFJ5YURNNWNVUk9OM0IwWm1wdlFtZzBlakJqTjIxc1RFeGxSM1JSTjFJMlFWVkNUMnhZTlV3elYyMXlTMmQ2U21WSFZrcDJMM2h1T1ZwMU1qUmpXVGd3VmxneWVsWm1iMloxVTBaUVJXSlVNR2xyZW5Sa1p6ZEVWbk5UUVdSWmQycHJjRVJMWVRZd2RtTmpTVXB2WVZWWmRWSTBWRGxzVFdKQlVucElURWc1WjBWdVp6VXhMekpQU1RSUFdHTnBjR013U25Wdk9XTldRM0Y0VjI5dFIzZHZkbkZ2U1ZOb2VEa3dhRm81ZVhsUlJFSTFUbGRCZUc1cFNTOHdObWR2YW5CcGNIRXpaSGM1ZFhrek1VTk5hR1IxWVd3M1NGbEZhME52VTFOd1IycHlWV0l5VTBkbE9IaHdVRTAyWWl0bFIxbE9jalp4WWpkMGVGaEtiREJHTVVkRlN6Sm5RemRuWW5OWlJYcG1ZaXQyWTFCTVZYWXplRTg1UlVZeVlscGtjMHhOSzA1ckwxaFdiMGxwY1ZGTVNEWlRiVWN4U2tGWFJYTkxXSE5ETTJReFpWUmlRV04xU25ONWVFSXhWbWRvTkVKdFYyc3lNSEJCYWtSWlIycHBRa1J1UnpaQlQyTkZhVzVOV2s1V2IxY3hPRVJxSzNsd1dXZG1jR05LVEVSWGVVdFZkall2UnpCVVR6RkViR1ZsYjBwRWVrVmpiblkwVEVFeFVXWTRaREpUU1d0TmRHd3pUakpJVjNsR1NGaDVUSE5oUW5oMVRFcGxjVlJNZDFabEx6TjVkVGhvTXpOek5HRm1UbkJXTkdKR05YcEZURzl3T1RoSk1qYzVjaXR4VTJSbFVrNU1PVVZxWjA5dVNsVXlVelpLTjFBeU4zRXlNMlFyY1VGM05rSkxTMk5uWlc1TGJWVmpOVk5yUkdrM2RtUktSR1pvYmsxVWJuSlFPVlJaVDJzckt5OVBiMDU1ZEZGeVJEQjBXbFlyVFhwVFVWRkRhRGh3VUVsTk9VeGpkVzA1WlVNcmNsSjVkR3MyTWt0RWQyMXhiMFl3UTB0Q2VWWjRiM0EwVFVkTlZYSlViemx5VUZwUFJuSmlPSEZRWld0ak5FOWtXRVpzZW5rNFltdEpiRk5PVUNzeU5ITlNURnAzVVRaS1lsSkVjMk5QVWtneFNIbElkSFJ2Y1hCT1kwbG9kWHBIYkZGNFNsTlBRVkY2VFVkM1RXOXpVSFpvY1U1VFIxUmFNbGRFYWt0REswOU5Sa3B0UkhSd1JGTndOM2x6YzJWMFpXNWtXSE5UYmtwWU5FdEplRU5TUlRaWVlqa3pSSEZST0haTFNsZExlR05sZG5VM1IzRkJXVk5QVlRoWlVsUjFTa3gyZDI1T2FqRnZOa1IxTkdkMllteDBkbVpaVWtobWNIZDRaMDVrWjB0S2IwUXJUamRJTjJkNVVYZElZa0ZrWm5KaVptUlZia0ppZGxWNU5uTlFTM1k1VlZoalNFTXpXVEJtY2pSWlpGTTVkWEE0YlhkeVJraHJTRkpwVGt4ek5GTkJVQ3RaVlhBd016ZEJLemhVUjBwRlZYRlFVMDlEV2xZeGQwdE9PWEZ1UTJOWmFXVjFZbVJJVURWeWIzQkVaa3QwVDNNeFFtaDVNMlpJUVVkNFVrWnFaMXBPYkM4NE1rTk1PWGMwZG1WNFRtZ3ZOWFIySzNOcVprcHZNa3RzVkRWWmNtcHlZakZ3Tm5Oc1JXRXJNVlJMWlVkaFVuQnZSMUJPVUN0ME5uZ3hZMFZzY0c1Mk5rNUZhR1UwU1hvd05sVjZWRGg2UVQwOS52TXhQRk5NQlk2V3VqRnYySlhqMUF1NV9CVkdwTTlhY20zOGdlWWhVN2FwR0NQTW9QVjlHMHRLR1NJYS1LZGpyUmtOdF9VR1dWay1nT2pvc2ZZS0pJUQ==" }
    return requests.post(authsite, data=data).cookies


def getClasses(subject, semester='201808', campus='COL', number='', title='',
               min_credits=1, max_credits='', level='%', term='30', times='%',
               location='%', start_hour=0, start_minute=0, end_hour=0,
               end_minute=0, days='dummy'):
    params = locals()
    coursesite = 'https://ssb.onecarolina.sc.edu/BANP/bwckschd.p_get_crse_unsec'
    allowed = { 'semester':  ("201341", "201401", "201405", "201408", "201501", "201505",
                       "201508", "201601", "201605", "201608", "201701", "201705",
                       "201708", "201801", "201805", "201808"),
                'campus': ('AIK', 'BFT', 'COL', 'LAN', 'SAL', 'SMT', "UNI", "UPS"),
                'subject': ("ACCT", "AERO", "AFAM", "ANES", "ANTH", "ARAB", "ARMY",
                            "ARTE", "ARTH", "ARTS", "ASLG", "ASTR", "ATEP", "BADM",
                            "BIOL", "BIOS", "BMEN", "BMSC", "CHEM", "CHIN", "CLAS",
                            "COLA", "COMD", "CPLT", "CRJU", "CSCE", "DANC", "DMED",
                            "DMSB", "ECHE", "ECIV", "ECON", "EDCE", "EDCS", "EDEC",
                            "EDEL", "EDET", "EDEX", "EDFI", "EDHE", "EDLP", "EDML",
                            "EDPY", "EDRD", "EDRM", "EDSE", "EDTE", "ELCT", "EMCH",
                            "EMED", "ENCP", "ENFS", "ENGL", "ENHS", "ENVR", "EPID",
                            "EXSC", "FAMS", "FINA", "FORL", "FPMD", "FREN", "GENE",
                            "GEOG", "GEOL", "GERM", "GLST", "GMED", "GRAD", "GREK",
                            "HGEN", "HIST", "HPEB", "HRSM", "HRTM", "HSPM", "IBUS",
                            "IDST", "INTL", "ITAL", "ITEC", "JAPA", "JOUR", "LASP",
                            "LATN", "LAWS", "LIBR", "LING", "MART", "MATH", "MBAD",
                            "MBIM", "MCBA", "MEDI", "MGMT", "MGSC", "MKTG", "MSCI",
                            "MUED", "MUSC", "MUSM", "NAVY", "NEUR", "NPSY", "NURS",
                            "OBGY", "OPTH", "ORSU", "PALM", "PAMB", "PATH", "PEDI",
                            "PEDU", "PHAR", "PHIL", "PHMY", "PHPH", "PHYS", "PHYT",
                            "PMDR", "POLI", "PORT", "PSYC", "PUBH", "RADI", "RCON",
                            "RELG", "RETL", "RHAB", "RUSS", "SAEL", "SCCP", "SCHC",
                            "SLIS", "SMED", "SOCY", "SOST", "SOWK", "SPAN", "SPCH",
                            "SPTE", "STAT", "SURG", "THEA", "UNIV", "WGST"),
                'number': ('',) + tuple(range(1, 1000)),
                'level': ('%', 'GR', 'LW', 'MD', 'UG'),
                'term': ("1A", "1B", "10", "2A", "2B", "20", "3A", "3B", "30", "4A", "4B",
                         "40", "50", "6A", "6B", "60", "7A", "7B", "70", "8A", "8B", "80"),
                'times': ('%', 'E', 'O', 'W'),
                'location': ('%', "1A@S", "3FJ", "3GDC", "3GDG", "3GDI", "3GDL", "3GDR",
                             "8GRV", "8GRS", "7LAU", "3PLM", "3HNR", "1HNR", "1ONL",
                             "8HNR", "8PLM", "8SLC"),
                'start_hour': range(24),
                'start_minute': range(60),
                'end_hour': range(24),
                'end_minute': range(60),
                'days': ('m', 't', 'w', 'r', 'f', 's', 'u')
              }
    for p in params:
        # if p not in allowed, assume arbitrary input acceptable
        if params[p] != 'dummy' and p in allowed and params[p] not in allowed[p]:
            raise ValueError(str(params[p]) + 'not in ' + str(allowed[p]))

    ampm = (divmod(start_hour, 12), divmod(end_hour, 12))
    data = {"BEGIN_AP": ('p' if ampm[0][0] else 'a'),
            "BEGIN_HH": ampm[0][1],
            "BEGIN_MI": start_minute,
            "END_AP": ('p' if ampm[1][0] else 'a'),
            "END_HH": ampm[1][1],
            "END_MI": end_minute,
            "SEL_ATTR": ('dummy', location),
            "SEL_CAMP": ('dummy', campus),
            "SEL_CRSE": number,
            "SEL_DAY": days,
            "SEL_FROM_CRED": min_credits,
            "SEL_TO_CRED": max_credits,
            "SEL_INSM": 'dummy', "SEL_INSTR": 'dummy', "SEL_SCHD": "dummy",
            "SEL_LEVL": ('dummy', level),
            "SEL_PTRM": ('dummy', term),
            "SEL_SESS": ('dummy', times),
            "SEL_SUBJ": ('dummy', subject),
            "SEL_TITLE": title,
            "TERM_IN": ('dummy', semester)}
    
    from sys import stderr
    print(data, location, file=stderr, sep='\n')
    
    r = requests.post(coursesite, data=data)
    print(r.status_code, file=stderr)
    print_request(r.request, file=stderr)
    return r.text


def print_request(req, **kwargs):
    print(req.method, req.url, req.headers, req.body, sep='\n', **kwargs)

if __name__ == '__main__':
    print(getClasses('ACCT'))
