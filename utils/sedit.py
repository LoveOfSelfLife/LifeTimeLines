import sys
import re

rep1 = """        memory: 1Gi
      volumeMounts:
      - volumeName: azure-files-volume
        mountPath: /share
    volumes:
    - name: azure-files-volume
      storageType: AzureFile
      storageName: acaenvstorage
"""

def xform(s):
    lines = []
    ENV_PAT = '(.*-Dsolr.solr.home=).*(/share/solr/.*)'
    m = re.match(ENV_PAT, s)
    if m:
        lines.append(f'{m.group(1)}{m.group(2)}\n')
    else:
        if 'memory:' in s:
            lines.append(rep1)
        else:
            if 'volumes:' in s:
                pass
            else:
                if 'maxReplicas:' in s:
                    lines.append(s.replace("10", "1"))
                else:
                    lines.append(s)

    return lines

if __name__ == '__main__':
    for lin in sys.stdin:
        for lout in xform(lin):
            print(lout, end='')

