# from ndg-httpsclient (rev 8290)
from pyasn1.codec.der import decoder as der_decoder
from pyasn1.type import univ, constraint, char, namedtype, tag
import six

MAX = 64

class DirectoryString(univ.Choice):
    """ASN.1 Directory string class"""
    componentType = namedtype.NamedTypes(
        namedtype.NamedType(
            'teletexString', char.TeletexString().subtype(
                subtypeSpec=constraint.ValueSizeConstraint(1, MAX))),
        namedtype.NamedType(
            'printableString', char.PrintableString().subtype(
                subtypeSpec=constraint.ValueSizeConstraint(1, MAX))),
        namedtype.NamedType(
            'universalString', char.UniversalString().subtype(
                subtypeSpec=constraint.ValueSizeConstraint(1, MAX))),
        namedtype.NamedType(
            'utf8String', char.UTF8String().subtype(
                subtypeSpec=constraint.ValueSizeConstraint(1, MAX))),
        namedtype.NamedType(
            'bmpString', char.BMPString().subtype(
                subtypeSpec=constraint.ValueSizeConstraint(1, MAX))),
        namedtype.NamedType(
            'ia5String', char.IA5String().subtype(
                subtypeSpec=constraint.ValueSizeConstraint(1, MAX))),
        )


class AttributeValue(DirectoryString):
    """ASN.1 Attribute value"""


class AttributeType(univ.ObjectIdentifier):
    """ASN.1 Attribute type"""


class AttributeTypeAndValue(univ.Sequence):
    """ASN.1 Attribute type and value class"""
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('type', AttributeType()),
        namedtype.NamedType('value', AttributeValue()),
        )


class RelativeDistinguishedName(univ.SetOf):
    '''ASN.1 Realtive distinguished name'''
    componentType = AttributeTypeAndValue()

class RDNSequence(univ.SequenceOf):
    '''ASN.1 RDN sequence class'''
    componentType = RelativeDistinguishedName()


class Name(univ.Choice):
    '''ASN.1 name class'''
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('', RDNSequence()),
        )


class Extension(univ.Sequence):
    '''ASN.1 extension class'''
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('extnID', univ.ObjectIdentifier()),
        namedtype.DefaultedNamedType('critical', univ.Boolean('False')),
        namedtype.NamedType('extnValue', univ.OctetString()),
        )


class Extensions(univ.SequenceOf):
    '''ASN.1 extensions class'''
    componentType = Extension()
    sizeSpec = univ.SequenceOf.sizeSpec + constraint.ValueSizeConstraint(1, MAX)


class GeneralName(univ.Choice):
    '''ASN.1 configuration for X.509 certificate subjectAltNames fields'''
    componentType = namedtype.NamedTypes(
#        namedtype.NamedType('otherName', AnotherName().subtype(
#                            implicitTag=tag.Tag(tag.tagClassContext,
#                                                tag.tagFormatSimple, 0))),
        namedtype.NamedType('rfc822Name', char.IA5String().subtype(
                            implicitTag=tag.Tag(tag.tagClassContext,
                                                tag.tagFormatSimple, 1))),
        namedtype.NamedType('dNSName', char.IA5String().subtype(
                            implicitTag=tag.Tag(tag.tagClassContext,
                                                tag.tagFormatSimple, 2))),
#        namedtype.NamedType('x400Address', ORAddress().subtype(
#                            implicitTag=tag.Tag(tag.tagClassContext,
#                                                tag.tagFormatSimple, 3))),
        namedtype.NamedType('directoryName', Name().subtype(
                            implicitTag=tag.Tag(tag.tagClassContext,
                                                tag.tagFormatSimple, 4))),
#        namedtype.NamedType('ediPartyName', EDIPartyName().subtype(
#                            implicitTag=tag.Tag(tag.tagClassContext,
#                                                tag.tagFormatSimple, 5))),
        namedtype.NamedType('uniformResourceIdentifier', char.IA5String().subtype(
                            implicitTag=tag.Tag(tag.tagClassContext,
                                                tag.tagFormatSimple, 6))),
        namedtype.NamedType('iPAddress', univ.OctetString().subtype(
                            implicitTag=tag.Tag(tag.tagClassContext,
                                                tag.tagFormatSimple, 7))),
        namedtype.NamedType('registeredID', univ.ObjectIdentifier().subtype(
                            implicitTag=tag.Tag(tag.tagClassContext,
                                                tag.tagFormatSimple, 8))),
        )


class GeneralNames(univ.SequenceOf):
    '''Sequence of names for ASN.1 subjectAltNames settings'''
    componentType = GeneralName()
    sizeSpec = univ.SequenceOf.sizeSpec + constraint.ValueSizeConstraint(1, MAX)


class SubjectAltName(GeneralNames):
    '''ASN.1 implementation for subjectAltNames support'''

    # There is no limit to how many SAN certificates a certificate may have,
    #   however this needs to have some limit so we'll set an arbitrarily high
    #   limit.
    sizeSpec = univ.SequenceOf.sizeSpec + \
        constraint.ValueSizeConstraint(1, 1024)


# from urllib3
def get_subject_alt_name(peer_cert):
    # Search through extensions
    dns_name = []
    general_names = SubjectAltName()
    for i in range(peer_cert.get_extension_count()):
        ext = peer_cert.get_extension(i)
        ext_name = ext.get_short_name()
        if ext_name != six.b('subjectAltName'):
            continue

        # PyOpenSSL returns extension data in ASN.1 encoded form
        ext_dat = ext.get_data()
        decoded_dat = der_decoder.decode(ext_dat,
                                         asn1Spec=general_names)

        for name in decoded_dat:
            if not isinstance(name, SubjectAltName):
                continue
            for entry in range(len(name)):
                component = name.getComponentByPosition(entry)
                if component.getName() != 'dNSName':
                    continue
                dns_name.append(str(component.getComponent()))

    return dns_name
